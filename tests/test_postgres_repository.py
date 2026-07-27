from __future__ import annotations

import datetime as dt
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from inspection_records_search.infrastructure.postgres_repository import (  # noqa: E402
    PostgresInspectionRepository,
)


class PostgresInspectionRepositoryTests(unittest.TestCase):
    def test_main_detail_uses_latest_numeric_inspector_from_qr_history(self) -> None:
        repository = PostgresInspectionRepository(
            "postgresql://appearance",
            "postgresql://delivery",
        )
        calls: list[tuple[str, str, list[object] | None]] = []

        def fake_execute_query(dsn, sql, params=None):
            calls.append((dsn, sql, params))
            if sql.startswith("SELECT id, inspector_id") and (
                "FROM appearance_inspection_summaries" in sql
            ):
                return ([], [])
            if sql.startswith("SELECT MAX(inspection_date)"):
                return (["max"], [(dt.date(2026, 6, 25),)])
            if "FROM appearance_inspection_records" in sql:
                return (
                    [],
                    [
                        (
                            101,
                            "V001",
                            "P157275",
                            "7",
                            dt.datetime(2026, 7, 27),
                            dt.datetime(2026, 7, 27, 14, 7),
                            "T-110750L01",
                            "プラグ端子",
                            1234,
                            False,
                        ),
                        (
                            102,
                            "V001",
                            "P157329",
                            "1",
                            dt.datetime(2026, 7, 27),
                            dt.datetime(2026, 7, 27, 14, 50),
                            "MHL1232S-2",
                            "レンズ 枠固定枠",
                            100,
                            False,
                        ),
                    ],
                )
            if "FROM inspector_master" in sql:
                return (["inspector_id", "inspector_name"], [("V001", "中")])
            if "FROM qr_history" in sql:
                return (
                    ["production_lot_id", "inspector_id"],
                    [("P157275", "16")],
                )
            if "FROM numeric_inspector_master" in sql:
                return (
                    ["inspector_id", "inspector_name"],
                    [("16", "数値検査担当")],
                )
            raise AssertionError(f"Unexpected query: {sql}")

        with patch(
            "inspection_records_search.infrastructure.postgres_repository.execute_query",
            side_effect=fake_execute_query,
        ):
            headers, rows = repository.fetch_main_detail(
                dt.date(2026, 7, 27),
                dt.date(2026, 7, 27),
                "T-110750L01",
            )

        self.assertEqual(headers[-1], "数値検査員名")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][4], "P157275")
        self.assertEqual(rows[0][9], 43)
        self.assertEqual(rows[0][-1], "数値検査担当")

        main_dsn, main_sql, main_params = calls[0]
        self.assertEqual(main_dsn, "postgresql://appearance")
        self.assertNotIn("numeric_inspection_records", main_sql)
        self.assertEqual(
            main_params,
            [dt.date(2026, 7, 27), dt.date(2026, 7, 27), "T-110750L01"],
        )

        raw_call = next(call for call in calls if "FROM appearance_inspection_records" in call[1])
        self.assertEqual(
            raw_call[2],
            [dt.date(2026, 7, 27), dt.date(2026, 7, 27)],
        )

        qr_dsn, qr_sql, qr_params = next(
            call for call in calls if "FROM qr_history" in call[1]
        )
        self.assertEqual(qr_dsn, "postgresql://delivery")
        self.assertIn("FROM qr_history", qr_sql)
        self.assertIn("BTRIM(process_name) LIKE %s", qr_sql)
        self.assertIn("NULLIF(BTRIM(position), '') IS NOT NULL", qr_sql)
        self.assertIn("date_time DESC NULLS LAST, id DESC", qr_sql)
        self.assertEqual(qr_params, [["P157275"], "%数値検査%"])

    def test_main_detail_without_delivery_dsn_leaves_numeric_name_empty(self) -> None:
        repository = PostgresInspectionRepository("postgresql://appearance")

        def fake_execute_query(_dsn, sql, _params=None):
            if sql.startswith("SELECT id, inspector_id") and (
                "FROM appearance_inspection_summaries" in sql
            ):
                return (
                    [],
                    [
                        (
                            1,
                            "V001",
                            dt.datetime(2026, 7, 27),
                            "P157275",
                            "T-110750L01",
                            "プラグ端子",
                            "7",
                            1234,
                            43,
                            False,
                        )
                    ],
                )
            if sql.startswith("SELECT MAX(inspection_date)"):
                return (["max"], [(dt.date(2026, 7, 28),)])
            if "FROM inspector_master" in sql:
                return (["inspector_id", "inspector_name"], [("V001", "中")])
            raise AssertionError(f"Unexpected query: {sql}")

        with patch(
            "inspection_records_search.infrastructure.postgres_repository.execute_query",
            side_effect=fake_execute_query,
        ):
            headers, rows = repository.fetch_main_detail(
                dt.date(2026, 7, 27),
                dt.date(2026, 7, 27),
                None,
            )

        self.assertEqual(headers[-1], "数値検査員名")
        self.assertIsNone(rows[0][-1])

    def test_work_time_subtracts_access_break_periods(self) -> None:
        calculate = PostgresInspectionRepository._calculate_work_minutes

        self.assertEqual(
            calculate(
                dt.datetime(2026, 7, 27, 10, 0),
                dt.datetime(2026, 7, 27, 11, 0),
            ),
            55,
        )
        self.assertEqual(
            calculate(
                dt.datetime(2026, 7, 27, 12, 0),
                dt.datetime(2026, 7, 27, 13, 30),
            ),
            45,
        )

    def test_lot_aggregate_includes_calculated_live_summary(self) -> None:
        repository = PostgresInspectionRepository(
            "postgresql://appearance",
            "postgresql://delivery",
        )
        live_summary = (
            101,
            "V001",
            dt.datetime(2026, 7, 27),
            "P157275",
            "T-110750L01",
            "プラグ端子",
            "7",
            1234,
            43,
            False,
        )

        with (
            patch.object(
                repository,
                "_fetch_summary_rows",
                return_value=[live_summary],
            ),
            patch.object(
                repository,
                "_fetch_delivery_quantities",
                return_value={"P157275": 1234},
            ),
        ):
            headers, rows = repository.fetch_lot_aggregate(None, None)

        self.assertEqual(
            headers,
            ["生産ロットID", "工程NO", "品番", "品名", "数量", "作業時間"],
        )
        self.assertEqual(
            rows,
            [("P157275", "7", "T-110750L01", "プラグ端子", 1234, 43)],
        )


if __name__ == "__main__":
    unittest.main()
