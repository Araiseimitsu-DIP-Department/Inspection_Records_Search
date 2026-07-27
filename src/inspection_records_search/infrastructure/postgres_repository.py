"""PostgreSQL implementation of the inspection repository."""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
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
    """Repository using appearance_inspection_db and delivery_label_db tables."""

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
        summary_rows = self._fetch_summary_rows(
            date_from=date_from,
            date_to=date_to,
            inspector_id=inspector_id,
        )
        return (
            ["検査員ID", "日付", "ロットID", "品番", "品名", "工程", "数量", "時間"],
            [
                (
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                    row[7],
                    row[8],
                )
                for row in summary_rows
            ],
        )

    def fetch_main_detail(
        self,
        date_from: dt.date,
        date_to: dt.date,
        part_number: Optional[str],
    ) -> tuple[list[str], list[tuple]]:
        summary_rows = self._fetch_summary_rows(
            date_from=date_from,
            date_to=date_to,
            part_number=part_number,
        )
        inspector_names = self._fetch_inspector_names(
            {str(row[1]).strip() for row in summary_rows if row[1]}
        )
        rows = [
            (
                row[0],
                row[1],
                inspector_names.get(str(row[1]).strip()),
                row[2],
                row[3],
                row[4],
                row[5],
                row[6],
                row[7],
                row[8],
                row[9],
            )
            for row in summary_rows
        ]
        headers = [
            "ID",
            "検査員ID",
            "検査員名",
            "日付",
            "生産ロットID",
            "品番",
            "品名",
            "工程NO",
            "数量",
            "作業時間",
            "集計除外フラグ",
        ]
        numeric_inspector_names = self._fetch_numeric_inspector_names(
            {
                str(row[4]).strip()
                for row in rows
                if len(row) > 4 and row[4] is not None and str(row[4]).strip()
            }
        )
        headers.append("数値検査員名")
        return (
            headers,
            [
                (*row, numeric_inspector_names.get(str(row[4]).strip()))
                for row in rows
            ],
        )

    def _fetch_summary_rows(
        self,
        *,
        date_from: dt.date | None = None,
        date_to: dt.date | None = None,
        inspector_id: str | None = None,
        part_number: str | None = None,
        process_values: list[str] | None = None,
    ) -> list[tuple]:
        """Return stored summaries plus summaries calculated from live records."""
        sql = (
            "SELECT id, inspector_id, inspection_date, production_lot_id, "
            "product_code, product_name, process_no, quantity, work_time, "
            "aggregation_exclusion_flag "
            "FROM appearance_inspection_summaries"
        )
        wheres: list[str] = []
        params: list[object] = []
        if date_from is not None:
            wheres.append("inspection_date::date >= %s")
            params.append(date_from)
        if date_to is not None:
            wheres.append("inspection_date::date <= %s")
            params.append(date_to)
        if inspector_id:
            wheres.append("inspector_id = %s")
            params.append(inspector_id)
        if part_number and part_number.strip():
            wheres.append("product_code = %s")
            params.append(part_number.strip())
        if process_values:
            wheres.append("process_no::text = ANY(%s)")
            params.append(process_values)
        if wheres:
            sql += " WHERE " + " AND ".join(wheres)

        _headers, stored_rows = execute_query(self._dsn, sql, params)
        live_rows = self._calculate_live_summaries(
            date_from=date_from,
            date_to=date_to,
            inspector_id=inspector_id,
        )

        part_filter = part_number.strip() if part_number and part_number.strip() else None
        process_filter = set(process_values or [])
        if part_filter:
            live_rows = [
                row for row in live_rows if str(row[4] or "").strip() == part_filter
            ]
        if process_filter:
            live_rows = [
                row for row in live_rows if str(row[6] or "").strip() in process_filter
            ]

        stored_keys = {self._summary_key(row) for row in stored_rows}
        combined = list(stored_rows)
        combined.extend(
            row for row in live_rows if self._summary_key(row) not in stored_keys
        )
        combined.sort(
            key=lambda row: (
                self._as_date(row[2]) or dt.date.min,
                str(row[1] or ""),
                int(row[0] or 0),
            )
        )
        return combined

    def _calculate_live_summaries(
        self,
        *,
        date_from: dt.date | None,
        date_to: dt.date | None,
        inspector_id: str | None,
    ) -> list[tuple]:
        """Reproduce the Access work-time aggregation from live PostgreSQL rows."""
        _headers, cutoff_rows = execute_query(
            self._dsn,
            "SELECT MAX(inspection_date)::date FROM appearance_inspection_summaries",
        )
        cutoff = self._as_date(cutoff_rows[0][0]) if cutoff_rows and cutoff_rows[0] else None
        start_date = date_from
        if cutoff is not None and (start_date is None or cutoff > start_date):
            start_date = cutoff
        if date_to is not None and start_date is not None and start_date > date_to:
            return []

        sql = (
            "SELECT id, inspector_id, production_lot_id, process_no, "
            "inspection_date, time_at, product_code, product_name, quantity, "
            "aggregation_exclusion_flag "
            "FROM appearance_inspection_records"
        )
        wheres: list[str] = ["time_at IS NOT NULL"]
        params: list[object] = []
        if start_date is not None:
            wheres.append("inspection_date::date >= %s")
            params.append(start_date)
        if date_to is not None:
            wheres.append("inspection_date::date <= %s")
            params.append(date_to)
        if inspector_id:
            wheres.append("inspector_id = %s")
            params.append(inspector_id)
        sql += " WHERE " + " AND ".join(wheres)
        sql += " ORDER BY inspector_id, inspection_date::date, time_at, id"
        _headers, records = execute_query(self._dsn, sql, params)

        records_by_person_date: dict[tuple[str, dt.date], list[tuple]] = defaultdict(list)
        for record in records:
            inspection_date = self._as_date(record[4])
            if not record[1] or inspection_date is None:
                continue
            records_by_person_date[(str(record[1]).strip(), inspection_date)].append(
                record
            )

        grouped: dict[tuple[str, dt.date, str, str], dict[str, object]] = {}
        for (record_inspector, inspection_date), daily_records in records_by_person_date.items():
            for current, following in zip(daily_records, daily_records[1:]):
                lot = str(current[2] or "").strip()
                process_no = str(current[3] or "").strip()
                if (lot and lot.startswith("T")) or (not lot and process_no == "0"):
                    continue
                started_at = self._combine_inspection_time(inspection_date, current[5])
                ended_at = self._combine_inspection_time(inspection_date, following[5])
                if started_at is None or ended_at is None:
                    continue
                work_time = self._calculate_work_minutes(started_at, ended_at)
                key = (record_inspector, inspection_date, lot, process_no)
                item = grouped.setdefault(
                    key,
                    {
                        "id": current[0],
                        "product_code": current[6],
                        "product_name": current[7],
                        "quantity": current[8],
                        "work_time": 0,
                        "excluded": False,
                    },
                )
                item["work_time"] = int(item["work_time"] or 0) + work_time
                item["excluded"] = bool(item["excluded"]) or bool(current[9])

        rows: list[tuple] = []
        for (record_inspector, inspection_date, lot, process_no), item in grouped.items():
            rows.append(
                (
                    item["id"],
                    record_inspector,
                    dt.datetime.combine(inspection_date, dt.time.min),
                    lot or None,
                    item["product_code"],
                    item["product_name"],
                    process_no,
                    item["quantity"],
                    item["work_time"],
                    item["excluded"],
                )
            )
        return rows

    def _fetch_inspector_names(self, inspector_ids: set[str]) -> dict[str, str]:
        if not inspector_ids:
            return {}
        sql = (
            "SELECT BTRIM(inspector_id), BTRIM(inspector_name) "
            "FROM inspector_master WHERE BTRIM(inspector_id) = ANY(%s)"
        )
        _headers, rows = execute_query(self._dsn, sql, [sorted(inspector_ids)])
        return {
            str(inspector_id).strip(): str(inspector_name).strip()
            for inspector_id, inspector_name in rows
            if inspector_id is not None and inspector_name is not None
        }

    @staticmethod
    def _summary_key(row: tuple) -> tuple[str, dt.date | None, str, str]:
        return (
            str(row[1] or "").strip(),
            PostgresInspectionRepository._as_date(row[2]),
            str(row[3] or "").strip(),
            str(row[6] or "").strip(),
        )

    @staticmethod
    def _as_date(value: object) -> dt.date | None:
        if isinstance(value, dt.datetime):
            return value.date()
        if isinstance(value, dt.date):
            return value
        if value is None:
            return None
        try:
            return dt.date.fromisoformat(str(value)[:10])
        except ValueError:
            return None

    @staticmethod
    def _combine_inspection_time(
        inspection_date: dt.date,
        value: object,
    ) -> dt.datetime | None:
        if isinstance(value, dt.datetime):
            return dt.datetime.combine(inspection_date, value.time())
        if isinstance(value, dt.time):
            return dt.datetime.combine(inspection_date, value)
        if value is None:
            return None
        try:
            parsed_time = dt.time.fromisoformat(str(value).split()[-1])
        except ValueError:
            return None
        return dt.datetime.combine(inspection_date, parsed_time)

    @staticmethod
    def _calculate_work_minutes(start: dt.datetime, end: dt.datetime) -> int:
        start = start.replace(second=0, microsecond=0)
        end = end.replace(second=0, microsecond=0)
        minutes = int((end - start).total_seconds() // 60)
        for break_start, break_end in (
            (dt.time(10, 30), dt.time(10, 35)),
            (dt.time(12, 15), dt.time(13, 0)),
            (dt.time(15, 0), dt.time(15, 10)),
        ):
            if start.time() <= break_start and end.time() >= break_end:
                minutes -= (
                    dt.datetime.combine(start.date(), break_end)
                    - dt.datetime.combine(start.date(), break_start)
                ).seconds // 60
        return max(0, minutes)

    def _fetch_numeric_inspector_names(self, lots: set[str]) -> dict[str, str]:
        """Return the latest numeric inspector name for each production lot."""
        if not self._delivery_label_dsn or not lots:
            return {}

        qr_sql = (
            "SELECT DISTINCT ON (BTRIM(production_lot_id)) "
            "BTRIM(production_lot_id), BTRIM(position) "
            "FROM qr_history "
            "WHERE BTRIM(production_lot_id) = ANY(%s) "
            "AND BTRIM(process_name) LIKE %s "
            "AND NULLIF(BTRIM(position), '') IS NOT NULL "
            "ORDER BY BTRIM(production_lot_id), date_time DESC NULLS LAST, id DESC"
        )
        _headers, qr_rows = execute_query(
            self._delivery_label_dsn,
            qr_sql,
            [sorted(lots), "%数値検査%"],
        )
        inspector_by_lot = {
            str(lot).strip(): str(inspector_id).strip()
            for lot, inspector_id in qr_rows
            if lot is not None
            and inspector_id is not None
            and str(lot).strip()
            and str(inspector_id).strip()
        }
        inspector_ids = sorted(set(inspector_by_lot.values()))
        if not inspector_ids:
            return {}

        master_sql = (
            "SELECT BTRIM(inspector_id), BTRIM(inspector_name) "
            "FROM numeric_inspector_master "
            "WHERE BTRIM(inspector_id) = ANY(%s)"
        )
        _headers, master_rows = execute_query(
            self._dsn,
            master_sql,
            [inspector_ids],
        )
        name_by_id = {
            str(inspector_id).strip(): str(inspector_name).strip()
            for inspector_id, inspector_name in master_rows
            if inspector_id is not None
            and inspector_name is not None
            and str(inspector_id).strip()
        }
        return {
            lot: name_by_id[inspector_id]
            for lot, inspector_id in inspector_by_lot.items()
            if inspector_id in name_by_id
        }

    def fetch_koutei_distinct_values(self) -> list[str]:
        sql = (
            "SELECT DISTINCT process_no FROM ("
            "SELECT process_no FROM appearance_inspection_summaries "
            "UNION ALL SELECT process_no FROM appearance_inspection_records"
            ") processes "
            "WHERE NULLIF(BTRIM(process_no::text), '') IS NOT NULL ORDER BY process_no"
        )
        _headers, rows = execute_query(self._dsn, sql)
        return [str(row[0]).strip() for row in rows if row and row[0] is not None]

    def fetch_lot_aggregate(
        self,
        hinban: Optional[str],
        koutei: Optional[str],
    ) -> tuple[list[str], list[tuple]]:
        process_values: list[str] | None = None
        if koutei and koutei.strip():
            process_values = _expand_koutei_match_values(koutei)
        summary_rows = self._fetch_summary_rows(
            part_number=hinban,
            process_values=process_values,
        )

        grouped: dict[tuple[str, str, str, str], dict[str, object]] = {}
        lots: set[str] = set()
        for row in summary_rows:
            lot = "" if row[3] is None else str(row[3]).strip()
            if not lot:
                continue
            process_no = "" if row[6] is None else str(row[6]).strip()
            product_code = "" if row[4] is None else str(row[4]).strip()
            product_name = "" if row[5] is None else str(row[5]).strip()
            quantity = row[7]
            work_time = row[8]
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
            "SELECT DISTINCT ON (production_lot_id) production_lot_id, quantity "
            "FROM delivery_label_history "
            "WHERE production_lot_id = ANY(%s) AND quantity IS NOT NULL "
            "ORDER BY production_lot_id, instruction_date DESC NULLS LAST, "
            "printed_date DESC NULLS LAST, completed_date DESC NULLS LAST"
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
