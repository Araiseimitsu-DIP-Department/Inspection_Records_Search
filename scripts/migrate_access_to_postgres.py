"""Migrate Access inspection records to PostgreSQL."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from inspection_records_search.config import (
    get_access_db_path,
    get_application_base_dir,
    get_postgres_dsn,
    load_env,
)
from inspection_records_search.infrastructure.access_gateway import execute_query


@dataclass(frozen=True)
class TableSpec:
    access_table: str
    postgres_table: str
    columns: tuple[tuple[str, str], ...]

    @property
    def access_columns(self) -> tuple[str, ...]:
        return tuple(c[0] for c in self.columns)

    @property
    def postgres_columns(self) -> tuple[str, ...]:
        return tuple(c[1] for c in self.columns)


TABLES: tuple[TableSpec, ...] = (
    TableSpec(
        "t_外観検査記録",
        "appearance_records",
        (
            ("ID", "id"),
            ("検査員ID", "inspector_id"),
            ("生産ロットID", "production_lot_id"),
            ("工程NO", "process_no"),
            ("日付", "inspection_date"),
            ("時刻", "inspection_time"),
            ("品番", "part_number"),
            ("品名", "part_name"),
            ("客先", "customer_name"),
            ("数量", "quantity"),
            ("更新フラグ", "updated_flag"),
            ("集計除外フラグ", "excluded_from_summary"),
        ),
    ),
    TableSpec(
        "t_外観検査集計",
        "appearance_summary",
        (
            ("ID", "id"),
            ("検査員ID", "inspector_id"),
            ("日付", "inspection_date"),
            ("生産ロットID", "production_lot_id"),
            ("品番", "part_number"),
            ("品名", "part_name"),
            ("工程NO", "process_no"),
            ("数量", "quantity"),
            ("作業時間", "work_minutes"),
            ("集計除外フラグ", "excluded_from_summary"),
        ),
    ),
    TableSpec(
        "t_工程マスタ",
        "process_master",
        (("工程NO", "process_no"), ("工程名", "process_name")),
    ),
    TableSpec(
        "t_数値検査員マスタ",
        "numeric_inspector_master",
        (
            ("検査員ID", "inspector_id"),
            ("検査員名", "inspector_name"),
            ("区別", "category"),
            ("表示フラグ", "visible"),
        ),
    ),
    TableSpec(
        "t_数値検査記録",
        "numeric_inspection_records",
        (
            ("ID", "id"),
            ("日付時刻", "recorded_at"),
            ("生産ロットID", "production_lot_id"),
            ("検査員ID", "inspector_id"),
            ("工程名", "process_name"),
            ("号機", "machine_no"),
        ),
    ),
    TableSpec(
        "t_検査員マスタ",
        "inspector_master",
        (
            ("検査員ID", "inspector_id"),
            ("検査員名", "inspector_name"),
            ("表示位置", "display_order"),
            ("チーム", "team"),
            ("ふりがな", "kana"),
        ),
    ),
    TableSpec(
        "t_現品票検索用",
        "product_catalog",
        (
            ("生産ロットID", "production_lot_id"),
            ("号機", "machine_no"),
            ("品番", "part_number"),
            ("品名", "part_name"),
            ("客先", "customer_name"),
            ("指示日", "instruction_date"),
            ("数量", "quantity"),
        ),
    ),
)

IDENTITY_TABLES = (
    "appearance_records",
    "appearance_summary",
    "numeric_inspection_records",
)


def _schema_path(file_name: str) -> Path:
    return get_application_base_dir() / "database" / "postgresql" / file_name


def _read_sql(file_name: str) -> str:
    return _schema_path(file_name).read_text(encoding="utf-8")


def _select_sql(table: str, columns: tuple[str, ...]) -> str:
    column_list = ", ".join(f"[{c}]" for c in columns)
    return f"SELECT {column_list} FROM [{table}]"


def _insert_sql(table: str, columns: tuple[str, ...]) -> sql.Composed:
    placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in columns)
    return sql.SQL("INSERT INTO {} ({}) OVERRIDING SYSTEM VALUE VALUES ({})").format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(c) for c in columns),
        placeholders,
    )


def _print_counts(access_path: str) -> None:
    for spec in TABLES:
        _, rows = execute_query(access_path, f"SELECT COUNT(*) FROM [{spec.access_table}]")
        print(f"{spec.access_table}: {int(rows[0][0]):,} rows")


def _apply_sql(conn: psycopg.Connection, file_name: str) -> None:
    with conn.cursor() as cur:
        cur.execute(_read_sql(file_name))
    conn.commit()


def _truncate(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("TRUNCATE {} RESTART IDENTITY CASCADE").format(
                sql.SQL(", ").join(sql.Identifier(t.postgres_table) for t in TABLES)
            )
        )
    conn.commit()


def _reset_identity(conn: psycopg.Connection, table: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                "SELECT setval(pg_get_serial_sequence(%s, %s), "
                "COALESCE((SELECT MAX({}) FROM {}), 1), "
                "COALESCE((SELECT MAX({}) FROM {}), 0) > 0)"
            ).format(
                sql.Identifier("id"),
                sql.Identifier(table),
                sql.Identifier("id"),
                sql.Identifier(table),
            ),
            [table, "id"],
        )


def _insert_missing_numeric_inspectors(conn: psycopg.Connection) -> int:
    """Add non-visible placeholder master rows for legacy numeric inspector IDs."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO numeric_inspector_master
                (inspector_id, inspector_name, category, visible)
            SELECT DISTINCT r.inspector_id, '未登録', '補正', false
            FROM numeric_inspection_records r
            LEFT JOIN numeric_inspector_master m
                ON r.inspector_id = m.inspector_id
            WHERE r.inspector_id IS NOT NULL
              AND m.inspector_id IS NULL
            """
        )
        return cur.rowcount


def _copy_table(
    conn: psycopg.Connection,
    access_path: str,
    spec: TableSpec,
    batch_size: int,
) -> int:
    _, rows = execute_query(access_path, _select_sql(spec.access_table, spec.access_columns))
    statement = _insert_sql(spec.postgres_table, spec.postgres_columns)
    with conn.cursor() as cur:
        for idx in range(0, len(rows), batch_size):
            cur.executemany(statement, rows[idx : idx + batch_size])
    conn.commit()
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Read Access counts only.")
    parser.add_argument("--apply-schema", action="store_true", help="Run 001_schema.sql first.")
    parser.add_argument("--truncate", action="store_true", help="Truncate destination tables.")
    parser.add_argument("--indexes", action="store_true", help="Run 002_indexes.sql after import.")
    parser.add_argument("--constraints", action="store_true", help="Run 003_constraints.sql after import.")
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()

    load_env()
    access_path = get_access_db_path()
    dsn = get_postgres_dsn()
    if not access_path:
        raise SystemExit("ACCESS_DB_PATH is not set.")
    if not args.dry_run and not dsn:
        raise SystemExit("POSTGRES_CONNECTION_URL is not set.")

    print(f"Access: {access_path}")
    _print_counts(access_path)
    if args.dry_run:
        return 0

    with psycopg.connect(dsn) as conn:
        schema = (os.getenv("POSTGRES_SCHEMA") or "public").strip() or "public"
        with conn.cursor() as cur:
            cur.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        if args.apply_schema:
            _apply_sql(conn, "001_schema.sql")
        if args.truncate:
            _truncate(conn)
        for spec in TABLES:
            count = _copy_table(conn, access_path, spec, args.batch_size)
            print(f"imported {spec.postgres_table}: {count:,} rows")
        for table in IDENTITY_TABLES:
            _reset_identity(conn, table)
        inserted = _insert_missing_numeric_inspectors(conn)
        if inserted:
            print(f"inserted numeric_inspector_master placeholders: {inserted:,} rows")
        conn.commit()
        if args.indexes:
            _apply_sql(conn, "002_indexes.sql")
        if args.constraints:
            _apply_sql(conn, "003_constraints.sql")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
