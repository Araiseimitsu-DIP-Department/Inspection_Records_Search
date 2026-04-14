"""Repository interfaces used by the application layer."""

from __future__ import annotations

from typing import Protocol

from inspection_records_search.domain.models import TableData


class InspectionRepository(Protocol):
    def fetch_inspectors(self) -> TableData: ...

    def fetch_personal_records(
        self, inspector_id: str, date_from, date_to
    ) -> TableData: ...

    def fetch_personal_summary(
        self, inspector_id: str, date_from, date_to
    ) -> TableData: ...

    def fetch_main_detail(
        self, date_from, date_to, part_number
    ) -> TableData: ...

    def fetch_koutei_distinct_values(self) -> list[str]: ...

    def fetch_lot_aggregate(
        self, part_number, process_value
    ) -> TableData: ...
