"""PostgreSQL repository stub for future migration."""

from __future__ import annotations

import datetime as dt
from typing import Optional

from inspection_records_search.shared.errors import ConfigurationError


class PostgresInspectionRepository:
    """Placeholder implementation to keep the migration seam explicit."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _not_ready(self) -> ConfigurationError:
        return ConfigurationError(
            "DATABASE_BACKEND=postgres は設定済みですが、PostgreSQL 実装は未接続です。"
        )

    def fetch_inspectors(self):
        raise self._not_ready()

    def fetch_personal_records(
        self,
        inspector_id: str,
        date_from: dt.date,
        date_to: dt.date,
    ):
        raise self._not_ready()

    def fetch_personal_summary(
        self,
        inspector_id: str,
        date_from: dt.date,
        date_to: dt.date,
    ):
        raise self._not_ready()

    def fetch_main_detail(
        self,
        date_from: dt.date,
        date_to: dt.date,
        part_number: Optional[str],
    ):
        raise self._not_ready()

    def fetch_koutei_distinct_values(self) -> list[str]:
        raise self._not_ready()

    def fetch_lot_aggregate(
        self,
        hinban: Optional[str],
        koutei: Optional[str],
    ):
        raise self._not_ready()
