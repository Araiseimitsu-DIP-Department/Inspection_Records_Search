"""現品票検索DBをAccessからPostgreSQLへ忠実に移行する対象専用スクリプト。

このファイルは .docs/delivery_label_search_db 専用です。
Access側は読み取りのみとし、PostgreSQL側に既存の移行先テーブルがある場合は
削除・TRUNCATE・上書きをせず停止します。
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pyodbc
import psycopg2
from dotenv import dotenv_values
from psycopg2.extras import execute_values


TARGET_DIR = Path(__file__).resolve().parent
META_FILE = "現品票検索DB_meta.json"
RESULT_FILE = "migration_result_delivery_label_search_db.md"
MAPPING_FILE = "migration_mapping_delivery_label_search_db.md"
ERROR_LOG_FILE = "migration_error_delivery_label_search_db.log"
DEFAULT_SCHEMA = "public"
DEFAULT_BATCH_SIZE = 1000

ACCESS_TABLE_NAME = "t_現品票検索用"
POSTGRES_TABLE_NAME = "delivery_label_search"

COLUMN_NAME_MAP = {
    "生産ロットID": "production_lot_id",
    "号機": "machine_no",
    "品番": "product_code",
    "品名": "product_name",
    "客先": "customer",
    "指示日": "instruction_date",
    "数量": "quantity",
}

IMPORTANT_COLUMN_NAMES = {
    "production_lot_id",
    "machine_no",
    "product_code",
    "product_name",
    "customer",
    "instruction_date",
    "quantity",
}


@dataclass(frozen=True)
class ColumnMapping:
    access_name: str
    postgres_name: str
    access_type: str
    postgres_type: str
    nullable: bool
    note: str


@dataclass(frozen=True)
class TableMapping:
    access_name: str
    postgres_name: str
    table_type: str
    access_row_count: int
    columns: list[ColumnMapping]
    primary_key: list[str]
    indexes: list[dict[str, Any]]


@dataclass
class MigrationResult:
    table: TableMapping
    access_row_count: int | None = None
    postgres_row_count: int = 0
    inserted_row_count: int = 0
    status: str = "未実行"
    error: str = ""


def main() -> int:
    args = parse_args()
    setup_logging(TARGET_DIR / ERROR_LOG_FILE)

    try:
        env = load_env(TARGET_DIR / ".env")
        meta = load_meta(TARGET_DIR / META_FILE)
        access_db_path = resolve_access_db_path(env, meta)
        mapping = build_mapping(meta)
        write_mapping(TARGET_DIR / MAPPING_FILE, env, meta, mapping, None)

        if args.verify_only:
            result = verify_counts(env["DATABASE_URL"], access_db_path, mapping, args.schema)
        else:
            result = migrate(
                database_url=env["DATABASE_URL"],
                access_db_path=access_db_path,
                mapping=mapping,
                schema=args.schema,
                batch_size=args.batch_size,
            )

        write_mapping(TARGET_DIR / MAPPING_FILE, env, meta, mapping, result)
        write_result(TARGET_DIR / RESULT_FILE, access_db_path, result)
        return 0 if result.status == "成功" else 1
    except Exception:
        logging.exception("移行処理が失敗しました")
        return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="現品票検索DBをPostgreSQLへ移行")
    parser.add_argument("--schema", default=DEFAULT_SCHEMA, help="PostgreSQLスキーマ名")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="一括投入件数")
    parser.add_argument("--verify-only", action="store_true", help="投入せずAccess/PostgreSQL件数だけ再確認")
    return parser.parse_args()


def setup_logging(error_log_path: Path) -> None:
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(error_log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def load_env(env_path: Path) -> dict[str, str]:
    values = {key: value for key, value in dotenv_values(env_path).items() if value is not None}
    missing = [key for key in ("DATABASE_URL", "ACCESS_DB_PATH") if not values.get(key)]
    if missing:
        raise ValueError(f".envの必須項目が不足しています: {', '.join(missing)}")
    return values


def load_meta(meta_path: Path) -> dict[str, Any]:
    if not meta_path.exists():
        raise FileNotFoundError(f"メタJSONが見つかりません: {meta_path}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def resolve_access_db_path(env: dict[str, str], meta: dict[str, Any]) -> Path:
    env_path = Path(env["ACCESS_DB_PATH"])
    if env_path.exists():
        return env_path

    meta_path = Path(meta.get("database_path", ""))
    if meta_path.exists():
        logging.warning("ACCESS_DB_PATHが存在しないため、メタJSONのAccess DBパスを使用します")
        return meta_path

    raise FileNotFoundError(f"Access DBが見つかりません: {env_path}")


def build_mapping(meta: dict[str, Any]) -> TableMapping:
    tables = [table for table in meta["tables"] if table["name"] == ACCESS_TABLE_NAME]
    if len(tables) != 1:
        raise ValueError(f"移行対象テーブルを1件に特定できません: {ACCESS_TABLE_NAME}")

    table = tables[0]
    columns = [
        ColumnMapping(
            access_name=column["name"],
            postgres_name=COLUMN_NAME_MAP.get(column["name"], f"unknown_{index}"),
            access_type=column["access_type"],
            postgres_type=to_postgres_type(column),
            nullable=bool(column["nullable"]),
            note=build_column_note(column),
        )
        for index, column in enumerate(table["columns"], start=1)
    ]
    unknown_columns = [column.access_name for column in columns if column.postgres_name.startswith("unknown_")]
    if unknown_columns:
        joined = ", ".join(unknown_columns)
        raise ValueError(f"未定義のカラム名があります。推測せず停止します: {joined}")

    return TableMapping(
        access_name=table["name"],
        postgres_name=POSTGRES_TABLE_NAME,
        table_type=table["table_type"],
        access_row_count=int(table["row_count"] or 0),
        columns=columns,
        primary_key=table.get("primary_key", []),
        indexes=table.get("indexes", []),
    )


def to_postgres_type(column: dict[str, Any]) -> str:
    access_type = column["access_type"]
    size = column.get("column_size")
    if access_type in {"VARCHAR", "WVARCHAR"}:
        return f"VARCHAR({size})" if size else "TEXT"
    if access_type == "INTEGER":
        return "INTEGER"
    if access_type in {"DATETIME", "DATE"}:
        return "TIMESTAMP"
    if access_type in {"DOUBLE", "REAL", "FLOAT"}:
        return "DOUBLE PRECISION"
    if access_type in {"NUMERIC", "DECIMAL", "CURRENCY"}:
        return "NUMERIC"
    if access_type == "BIT":
        return "BOOLEAN"
    return column.get("postgres_type_hint") or "TEXT"


def build_column_note(column: dict[str, Any]) -> str:
    if column["name"] == "数量":
        return "NULLが存在するためNULL許可のINTEGERで保持"
    if column["access_type"] == "DATETIME":
        return "Accessの日付をtimestampで保持"
    return ""


def migrate(
    database_url: str,
    access_db_path: Path,
    mapping: TableMapping,
    schema: str,
    batch_size: int,
) -> MigrationResult:
    result = MigrationResult(table=mapping)
    access_connection = connect_access(access_db_path)
    postgres_connection = psycopg2.connect(database_url)
    try:
        postgres_connection.autocommit = False
        ensure_no_existing_table(postgres_connection, schema, mapping.postgres_name)
        create_schema_and_table(postgres_connection, schema, mapping)
        migrate_table(access_connection, postgres_connection, schema, result, batch_size)
        postgres_connection.commit()
    except Exception:
        postgres_connection.rollback()
        raise
    finally:
        access_connection.close()
        postgres_connection.close()
    return result


def verify_counts(
    database_url: str,
    access_db_path: Path,
    mapping: TableMapping,
    schema: str,
) -> MigrationResult:
    result = MigrationResult(table=mapping)
    access_connection = connect_access(access_db_path)
    postgres_connection = psycopg2.connect(database_url)
    try:
        with postgres_connection.cursor() as postgres_cursor:
            result.access_row_count = count_access_rows(access_connection, mapping.access_name)
            result.postgres_row_count = count_postgres_rows(postgres_cursor, schema, mapping.postgres_name)
            result.inserted_row_count = result.postgres_row_count
            result.status = "成功" if result.access_row_count == result.postgres_row_count else "件数差異"
            logging.info(
                "件数確認: %s Access=%s PostgreSQL=%s",
                mapping.access_name,
                result.access_row_count,
                result.postgres_row_count,
            )
    finally:
        access_connection.close()
        postgres_connection.close()
    return result


def connect_access(access_db_path: Path) -> pyodbc.Connection:
    connection_string = (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={access_db_path};"
    )
    return pyodbc.connect(connection_string, autocommit=True)


def ensure_no_existing_table(
    connection: psycopg2.extensions.connection,
    schema: str,
    table_name: str,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass(%s)", (f"{schema}.{table_name}",))
        if cursor.fetchone()[0] is not None:
            raise RuntimeError(f"移行先テーブルが既に存在するため停止しました: {schema}.{table_name}")


def create_schema_and_table(
    connection: psycopg2.extensions.connection,
    schema: str,
    mapping: TableMapping,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {quote_identifier(schema)}")
        column_sql = ",\n    ".join(build_column_sql(column) for column in mapping.columns)
        table_name = qualified_name(schema, mapping.postgres_name)
        cursor.execute(f"CREATE TABLE {table_name} (\n    {column_sql}\n)")
        cursor.execute(
            f"COMMENT ON TABLE {table_name} IS %s",
            (f"元Accessテーブル: {mapping.access_name}",),
        )
        for column in mapping.columns:
            cursor.execute(
                f"COMMENT ON COLUMN {table_name}.{quote_identifier(column.postgres_name)} IS %s",
                (f"元Accessカラム: {column.access_name}",),
            )


def build_column_sql(column: ColumnMapping) -> str:
    nullable_sql = "" if column.nullable else " NOT NULL"
    return f"{quote_identifier(column.postgres_name)} {column.postgres_type}{nullable_sql}"


def migrate_table(
    access_connection: pyodbc.Connection,
    postgres_connection: psycopg2.extensions.connection,
    schema: str,
    result: MigrationResult,
    batch_size: int,
) -> None:
    mapping = result.table
    access_columns = [column.access_name for column in mapping.columns]
    postgres_columns = [column.postgres_name for column in mapping.columns]
    select_sql = build_access_select_sql(mapping.access_name, access_columns)
    insert_sql = build_insert_sql(schema, mapping.postgres_name, postgres_columns)

    logging.info("移行開始: %s -> %s", mapping.access_name, mapping.postgres_name)
    try:
        result.access_row_count = count_access_rows(access_connection, mapping.access_name)
        access_cursor = access_connection.cursor()
        access_cursor.execute(select_sql)
        with postgres_connection.cursor() as postgres_cursor:
            while True:
                rows = access_cursor.fetchmany(batch_size)
                if not rows:
                    break
                values = [tuple(normalize_value(value) for value in row) for row in rows]
                execute_values(postgres_cursor, insert_sql, values, page_size=batch_size)
                result.inserted_row_count += len(values)
            result.postgres_row_count = count_postgres_rows(postgres_cursor, schema, mapping.postgres_name)
        result.status = "成功" if result.postgres_row_count == result.access_row_count else "件数差異"
        logging.info(
            "移行完了: %s Access=%s PostgreSQL=%s",
            mapping.access_name,
            result.access_row_count,
            result.postgres_row_count,
        )
    except Exception as error:
        result.status = "失敗"
        result.error = str(error)
        logging.exception("テーブル移行失敗: %s", mapping.access_name)
        raise


def build_access_select_sql(table_name: str, column_names: list[str]) -> str:
    columns = ", ".join(f"[{column}]" for column in column_names)
    return f"SELECT {columns} FROM [{table_name}]"


def build_insert_sql(schema: str, table_name: str, column_names: list[str]) -> str:
    columns = ", ".join(quote_identifier(column) for column in column_names)
    return f"INSERT INTO {qualified_name(schema, table_name)} ({columns}) VALUES %s"


def count_access_rows(connection: pyodbc.Connection, table_name: str) -> int:
    cursor = connection.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
    return int(cursor.fetchone()[0])


def count_postgres_rows(cursor: psycopg2.extensions.cursor, schema: str, table_name: str) -> int:
    cursor.execute(f"SELECT COUNT(*) FROM {qualified_name(schema, table_name)}")
    return int(cursor.fetchone()[0])


def normalize_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value
    return value


def write_mapping(
    path: Path,
    env: dict[str, str],
    meta: dict[str, Any],
    mapping: TableMapping,
    result: MigrationResult | None,
) -> None:
    access_count = result.access_row_count if result and result.access_row_count is not None else mapping.access_row_count
    postgres_count = result.postgres_row_count if result else ""
    status = result.status if result else "移行前"
    lines = [
        "# Access → PostgreSQL 移行対応表",
        "",
        "## 1. 移行概要",
        "",
        f"- 対象Access DB：{meta.get('database_path', '')}",
        f"- 移行先PostgreSQL DB：{extract_database_name(env['DATABASE_URL'])}",
        "- 接続情報：",
        "  - `.env` の DATABASE_URL を参照",
        f"- 移行日：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "- 作成者：Codex",
        "- 備考：現品票検索用の1テーブルを忠実に移行。日本語名はPostgreSQL用に英語のスネークケースへ変換し、元名はコメントと本対応表で追跡可能。",
        "",
        "## 2. 移行対象テーブル一覧",
        "",
        "| No | Accessテーブル名 | PostgreSQLテーブル名 | 種別 | Access件数 | PostgreSQL件数 | 備考 |",
        "|---:|---|---|---|---:|---:|---|",
        f"| 1 | {mapping.access_name} | {mapping.postgres_name} | {mapping.table_type} | {access_count} | {postgres_count} | {status} |",
        "",
        "## 3. テーブル別カラム対応表",
        "",
        f"### Accessテーブル名：{mapping.access_name}",
        f"### PostgreSQLテーブル名：{mapping.postgres_name}",
        "",
        "| No | Accessカラム名 | Access型 | PostgreSQLカラム名 | PostgreSQL型 | NULL許可 | 備考 |",
        "|---:|---|---|---|---|---|---|",
    ]
    for index, column in enumerate(mapping.columns, start=1):
        nullable = "可" if column.nullable else "不可"
        lines.append(
            f"| {index} | {column.access_name} | {column.access_type} | {column.postgres_name} | "
            f"{column.postgres_type} | {nullable} | {column.note} |"
        )

    primary_key = ", ".join(mapping.primary_key) if mapping.primary_key else "検出なし"
    indexes = ", ".join(index.get("name", "") for index in mapping.indexes) or "検出なし"
    lines.extend(
        [
            "",
            "## 4. 主キー・インデックス情報",
            "",
            "| Accessテーブル名 | PostgreSQLテーブル名 | 主キー | インデックス | 備考 |",
            "|---|---|---|---|---|",
            f"| {mapping.access_name} | {mapping.postgres_name} | {primary_key} | {indexes} | FKは未検出 |",
            "",
            "## 5. 型変換ルール",
            "",
            "| Access型 | PostgreSQL型 | 備考 |",
            "|---|---|---|",
            "| VARCHAR | varchar(n) | Accessのサイズを維持 |",
            "| INTEGER | integer | 整数。NULLはNULLのまま保持 |",
            "| DATETIME | timestamp | Accessの日付を保持 |",
            "",
            "## 6. アプリ接続時の参照情報",
            "",
            "### 接続先",
            "",
            "```text",
            ".env の DATABASE_URL を使用",
            "```",
            "",
            "### 主に参照するテーブル",
            "",
            "| 用途 | PostgreSQLテーブル名 | 主なキー | 備考 |",
            "| -- | --------------- | ---- | -- |",
            f"| 現品票検索 | {mapping.postgres_name} | production_lot_id, product_code | 元 {mapping.access_name} |",
            "",
            "### 主要カラム",
            "",
            "| 用途 | PostgreSQLテーブル名 | PostgreSQLカラム名 | 元Accessカラム名 | 備考 |",
            "| -- | --------------- | -------------- | ----------- | -- |",
        ]
    )
    for column in mapping.columns:
        if column.postgres_name in IMPORTANT_COLUMN_NAMES:
            lines.append(
                f"| {infer_column_purpose(column)} | {mapping.postgres_name} | {column.postgres_name} | "
                f"{column.access_name} | Accessの値をそのまま保持 |"
            )

    lines.extend(["", "## 7. 注意事項・要確認事項", ""])
    lines.extend(build_caution_lines(meta))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_caution_lines(meta: dict[str, Any]) -> list[str]:
    lines = [
        "- AccessのFKメタデータはODBCドライバが返さなかったため、外部キー制約は作成していません。",
        "- 主キーはメタデータ上は検出なしです。",
        "- `数量` はAccess側にNULLが2件あるため、PostgreSQLでもNULL許可のintegerとして保持しています。",
        "- `.env` の `ACCESS_DB_PATH` が実ファイルを指していない場合は、メタJSONの `database_path` を使用しています。",
    ]
    for warning in meta.get("warnings", []):
        lines.append(f"- メタ抽出警告：{warning}")
    return lines


def write_result(path: Path, access_db_path: Path, result: MigrationResult) -> None:
    access_count = result.access_row_count if result.access_row_count is not None else result.table.access_row_count
    lines = [
        "# Access → PostgreSQL 移行結果",
        "",
        f"- 実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Access DB: {access_db_path}",
        "",
        "| Accessテーブル名 | PostgreSQLテーブル名 | Access件数 | PostgreSQL件数 | 投入済み件数 | 状態 | エラー |",
        "|---|---|---:|---:|---:|---|---|",
        f"| {result.table.access_name} | {result.table.postgres_name} | {access_count} | "
        f"{result.postgres_row_count} | {result.inserted_row_count} | {result.status} | {result.error} |",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def infer_column_purpose(column: ColumnMapping) -> str:
    purposes = {
        "production_lot_id": "生産ロット",
        "machine_no": "号機",
        "product_code": "品番",
        "product_name": "品名",
        "customer": "客先",
        "instruction_date": "指示日",
        "quantity": "数量",
    }
    return purposes.get(column.postgres_name, column.access_name)


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def qualified_name(schema: str, table_name: str) -> str:
    return f"{quote_identifier(schema)}.{quote_identifier(table_name)}"


def extract_database_name(database_url: str) -> str:
    parsed = urlparse(database_url)
    return parsed.path.lstrip("/") or "要確認"


if __name__ == "__main__":
    raise SystemExit(main())
