"""PostgreSQL implementation of the inspection repository."""

from __future__ import annotations

import datetime as dt
from contextlib import contextmanager
from typing import Iterator, Optional

import psycopg

from inspection_records_search.infrastructure.access_gateway import (
    _expand_koutei_match_values,
)
from inspection_records_search.shared.errors import (
    DataConversionError,
    DataIntegrityError,
    DatabaseQueryError,
    DatabaseUnavailableError,
)


@contextmanager
def postgres_connection(dsn: str) -> Iterator[psycopg.Connection]:
    conn = psycopg.connect(dsn)
    try:
        yield conn
    finally:
        conn.close()


def execute_query(
    dsn: str, sql: str, params: tuple | list | None = None
) -> tuple[list[str], list[tuple]]:
    """Run a SELECT query and return Access-compatible headers and rows."""
    params = params or ()
    try:
        with postgres_connection(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                columns = [c.name for c in cur.description] if cur.description else []
                rows = cur.fetchall()
                return columns, [tuple(r) for r in rows]
    except psycopg.DataError as e:
        raise DataConversionError(str(e)) from e
    except psycopg.IntegrityError as e:
        raise DataIntegrityError(str(e)) from e
    except psycopg.OperationalError as e:
        raise DatabaseUnavailableError(str(e)) from e
    except psycopg.Error as e:
        raise DatabaseQueryError(str(e)) from e


class PostgresInspectionRepository:
    """Repository using English PostgreSQL physical names."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def fetch_inspectors(self) -> tuple[list[str], list[tuple]]:
        sql = (
            'SELECT inspector_id AS "検査員ID", inspector_name AS "検査員名" '
            "FROM inspector_master ORDER BY inspector_id"
        )
        return execute_query(self._dsn, sql)

    def fetch_personal_records(
        self,
        inspector_id: str,
        date_from: dt.date,
        date_to: dt.date,
    ) -> tuple[list[str], list[tuple]]:
        sql = (
            'SELECT inspector_id AS "検査員ID", production_lot_id AS "生産ロットID", '
            'process_no AS "工程NO", inspection_date AS "日付", inspection_time AS "時刻", '
            'part_number AS "品番", part_name AS "品名", customer_name AS "客先" '
            "FROM appearance_records "
            "WHERE inspector_id = %s AND inspection_date::date >= %s "
            "AND inspection_date::date <= %s "
            "ORDER BY inspection_date, inspection_time"
        )
        return execute_query(self._dsn, sql, [inspector_id, date_from, date_to])

    def fetch_personal_summary(
        self,
        inspector_id: str,
        date_from: dt.date,
        date_to: dt.date,
    ) -> tuple[list[str], list[tuple]]:
        sql = (
            'SELECT inspector_id AS "検査員ID", production_lot_id AS "生産ロットID", '
            'process_no AS "工程NO", inspection_date AS "日付", part_number AS "品番", '
            'part_name AS "品名", work_minutes AS "作業時間", quantity AS "数量" '
            "FROM appearance_summary "
            "WHERE inspector_id = %s AND inspection_date::date >= %s "
            "AND inspection_date::date <= %s "
            "ORDER BY inspection_date, id"
        )
        return execute_query(self._dsn, sql, [inspector_id, date_from, date_to])

    def fetch_main_detail(
        self,
        date_from: dt.date,
        date_to: dt.date,
        part_number: Optional[str],
    ) -> tuple[list[str], list[tuple]]:
        sql = (
            'SELECT s.id AS "ID", s.inspector_id AS "検査員ID", '
            'm.inspector_name AS "検査員名", s.inspection_date AS "日付", '
            's.production_lot_id AS "生産ロットID", s.part_number AS "品番", '
            's.part_name AS "品名", s.process_no AS "工程NO", s.quantity AS "数量", '
            's.work_minutes AS "作業時間", s.excluded_from_summary AS "集計除外フラグ", '
            'nm.inspector_name AS "数値検査員名" '
            "FROM appearance_summary s "
            "LEFT JOIN inspector_master m ON s.inspector_id = m.inspector_id "
            "LEFT JOIN numeric_inspection_records nr "
            "ON s.production_lot_id = nr.production_lot_id "
            "LEFT JOIN numeric_inspector_master nm ON nr.inspector_id = nm.inspector_id "
            "WHERE s.inspection_date::date >= %s AND s.inspection_date::date <= %s"
        )
        params: list[object] = [date_from, date_to]
        if part_number and part_number.strip():
            sql += " AND s.part_number = %s"
            params.append(part_number.strip())
        sql += " ORDER BY s.inspection_date, s.inspector_id, s.id"
        return execute_query(self._dsn, sql, params)

    def fetch_koutei_distinct_values(self) -> list[str]:
        sql_candidates = (
            "SELECT DISTINCT process_no FROM production_lot_aggregate "
            "WHERE NULLIF(BTRIM(process_no::text), '') IS NOT NULL ORDER BY process_no",
            "SELECT DISTINCT process_no FROM appearance_summary "
            "WHERE NULLIF(BTRIM(process_no::text), '') IS NOT NULL ORDER BY process_no",
            "SELECT DISTINCT process_no FROM appearance_records "
            "WHERE NULLIF(BTRIM(process_no::text), '') IS NOT NULL ORDER BY process_no",
        )
        for query in sql_candidates:
            try:
                headers, rows = execute_query(self._dsn, query)
                if not headers:
                    continue
                out: list[str] = []
                seen: set[str] = set()
                for row in rows:
                    if not row or row[0] is None:
                        continue
                    value = str(row[0]).strip()
                    if value and value not in seen:
                        seen.add(value)
                        out.append(value)
                if out:
                    return out
            except Exception:
                continue
        return []

    def fetch_lot_aggregate(
        self,
        hinban: Optional[str],
        koutei: Optional[str],
    ) -> tuple[list[str], list[tuple]]:
        sql = (
            'SELECT production_lot_id AS "生産ロットID", process_no AS "工程NO", '
            'part_number AS "品番", part_name AS "品名", quantity AS "数量", '
            'total_work_minutes AS "作業時間の合計" '
            "FROM production_lot_aggregate"
        )
        wheres: list[str] = []
        params: list[object] = []
        if hinban and hinban.strip():
            wheres.append("part_number = %s")
            params.append(hinban.strip())
        if koutei and koutei.strip():
            values = _expand_koutei_match_values(koutei)
            wheres.append("process_no::text = ANY(%s)")
            params.append(values)
        if wheres:
            sql += " WHERE " + " AND ".join(wheres)
        sql += " ORDER BY production_lot_id, process_no"
        return execute_query(self._dsn, sql, params)
