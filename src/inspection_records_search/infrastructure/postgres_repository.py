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
    """Repository using appearance_inspection_db physical names."""

    def __init__(self, dsn: str, delivery_label_dsn: str = "") -> None:
        self._dsn = dsn
        self._delivery_label_dsn = delivery_label_dsn

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
            'inspection_date AS "日付", time_at AS "時刻", process_no AS "工程", '
            'product_code AS "品番", product_name AS "品名", customer AS "客先" '
            "FROM appearance_inspection_records "
            "WHERE inspector_id = %s AND inspection_date::date >= %s "
            "AND inspection_date::date <= %s "
            "ORDER BY inspection_date, time_at"
        )
        return execute_query(self._dsn, sql, [inspector_id, date_from, date_to])

    def fetch_personal_summary(
        self,
        inspector_id: str,
        date_from: dt.date,
        date_to: dt.date,
    ) -> tuple[list[str], list[tuple]]:
        sql = (
            'SELECT inspector_id AS "検査員ID", inspection_date AS "日付", '
            'production_lot_id AS "ロットID", product_code AS "品番", '
            'product_name AS "品名", process_no AS "工程", quantity AS "数量", '
            'work_time AS "時間" '
            "FROM appearance_inspection_summaries "
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
            's.production_lot_id AS "生産ロットID", s.product_code AS "品番", '
            's.product_name AS "品名", s.process_no AS "工程NO", s.quantity AS "数量", '
            's.work_time AS "作業時間", s.aggregation_exclusion_flag AS "集計除外フラグ", '
            'nm.inspector_name AS "数値検査員名" '
            "FROM appearance_inspection_summaries s "
            "LEFT JOIN inspector_master m ON s.inspector_id = m.inspector_id "
            "LEFT JOIN numeric_inspection_records nr "
            "ON s.production_lot_id = nr.production_lot_id "
            "LEFT JOIN numeric_inspector_master nm ON nr.inspector_id = nm.inspector_id "
            "WHERE s.inspection_date::date >= %s AND s.inspection_date::date <= %s"
        )
        params: list[object] = [date_from, date_to]
        if part_number and part_number.strip():
            sql += " AND s.product_code = %s"
            params.append(part_number.strip())
        sql += " ORDER BY s.inspection_date, s.inspector_id, s.id"
        return execute_query(self._dsn, sql, params)

    def fetch_koutei_distinct_values(self) -> list[str]:
        sql_candidates = (
            "SELECT DISTINCT process_no FROM appearance_inspection_summaries "
            "WHERE NULLIF(BTRIM(process_no::text), '') IS NOT NULL ORDER BY process_no",
            "SELECT DISTINCT process_no FROM appearance_inspection_records "
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
            "SELECT production_lot_id, process_no, product_code, product_name, "
            "quantity, work_time "
            "FROM appearance_inspection_summaries"
        )
        wheres: list[str] = []
        params: list[object] = []
        if hinban and hinban.strip():
            wheres.append("product_code = %s")
            params.append(hinban.strip())
        if koutei and koutei.strip():
            values = _expand_koutei_match_values(koutei)
            wheres.append("process_no::text = ANY(%s)")
            params.append(values)
        if wheres:
            sql += " WHERE " + " AND ".join(wheres)
        sql += " ORDER BY production_lot_id, process_no, product_code, product_name"
        _headers, detail_rows = execute_query(self._dsn, sql, params)

        grouped: dict[tuple[str, str, str, str], dict[str, object]] = {}
        lots: set[str] = set()
        for row in detail_rows:
            lot = "" if row[0] is None else str(row[0]).strip()
            process_no = "" if row[1] is None else str(row[1]).strip()
            product_code = "" if row[2] is None else str(row[2]).strip()
            product_name = "" if row[3] is None else str(row[3]).strip()
            quantity = row[4]
            work_time = row[5]
            key = (lot, process_no, product_code, product_name)
            item = grouped.setdefault(
                key,
                {
                    "fallback_quantity": quantity,
                    "total_work_time": 0,
                },
            )
            if item["fallback_quantity"] is None and quantity is not None:
                item["fallback_quantity"] = quantity
            item["total_work_time"] = int(item["total_work_time"] or 0) + int(work_time or 0)
            if lot:
                lots.add(lot)

        delivery_quantities = self._fetch_delivery_quantities(lots)
        rows = []
        for key in sorted(grouped, key=lambda k: (k[0], k[1])):
            lot, process_no, product_code, product_name = key
            item = grouped[key]
            rows.append(
                (
                    lot,
                    process_no,
                    product_code,
                    product_name,
                    delivery_quantities.get(lot, item["fallback_quantity"]),
                    item["total_work_time"],
                )
            )
        return (
            ["生産ロットID", "工程NO", "品番", "品名", "数量", "作業時間"],
            rows,
        )

    def _fetch_delivery_quantities(self, lots: set[str]) -> dict[str, int]:
        if not self._delivery_label_dsn or not lots:
            return {}
        sql = (
            "SELECT production_lot_id, quantity "
            "FROM delivery_label_search "
            "WHERE production_lot_id = ANY(%s)"
        )
        try:
            _headers, rows = execute_query(self._delivery_label_dsn, sql, [list(lots)])
        except Exception:
            return {}
        out: dict[str, int] = {}
        for lot, quantity in rows:
            if lot is None or quantity is None:
                continue
            out[str(lot).strip()] = int(quantity)
        return out
