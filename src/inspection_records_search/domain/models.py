"""Domain models for the inspection inquiry application."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import TypeAlias


TableData: TypeAlias = tuple[list[str], list[tuple]]


@dataclass(frozen=True, slots=True)
class DateRange:
    """Closed date range used by the use cases."""

    start: dt.date
    end: dt.date

    def validate(self) -> None:
        if self.start > self.end:
            raise ValueError("表示開始日が表示終了日より後になっています。")


@dataclass(frozen=True, slots=True)
class PersonalInquiryCriteria:
    inspector_id: str
    date_range: DateRange


@dataclass(frozen=True, slots=True)
class LotAggregateCriteria:
    part_number: str | None = None
    process_value: str | None = None


@dataclass(frozen=True, slots=True)
class MainDetailCriteria:
    date_range: DateRange
    part_number: str | None = None


@dataclass(frozen=True, slots=True)
class InspectorOption:
    inspector_id: str
    inspector_name: str


@dataclass(frozen=True, slots=True)
class ProcessOption:
    process_code: str
    process_name: str
