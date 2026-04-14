"""Use cases for the inspection inquiry application."""

from __future__ import annotations

import datetime as dt

from inspection_records_search.domain.models import DateRange
from inspection_records_search.domain.repositories import InspectionRepository


class InspectionUseCase:
    """Thin application service that coordinates the repository."""

    def __init__(self, repository: InspectionRepository) -> None:
        self._repository = repository

    def fetch_inspectors(self):
        return self._repository.fetch_inspectors()

    def fetch_personal_records(
        self,
        inspector_id: str,
        date_from: dt.date,
        date_to: dt.date,
    ):
        DateRange(date_from, date_to).validate()
        return self._repository.fetch_personal_records(
            inspector_id, date_from, date_to
        )

    def fetch_personal_summary(
        self,
        inspector_id: str,
        date_from: dt.date,
        date_to: dt.date,
    ):
        DateRange(date_from, date_to).validate()
        return self._repository.fetch_personal_summary(
            inspector_id, date_from, date_to
        )

    def fetch_main_detail(
        self,
        date_from: dt.date,
        date_to: dt.date,
        part_number: str | None,
    ):
        DateRange(date_from, date_to).validate()
        return self._repository.fetch_main_detail(
            date_from, date_to, part_number
        )

    def fetch_koutei_distinct_values(self) -> list[str]:
        return self._repository.fetch_koutei_distinct_values()

    def fetch_lot_aggregate(
        self,
        part_number: str | None,
        process_value: str | None,
    ):
        return self._repository.fetch_lot_aggregate(
            part_number, process_value
        )
