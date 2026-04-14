"""Compatibility wrapper around the application use case."""

from __future__ import annotations

from pathlib import Path

from inspection_records_search.application.inspection_use_case import (
    InspectionUseCase,
)
from inspection_records_search.config import get_application_base_dir, resolve_export_dir
from inspection_records_search.domain.repositories import InspectionRepository
from inspection_records_search.infrastructure.access_gateway import (
    DEFAULT_KOUTEI_FALLBACK,
)
from inspection_records_search.infrastructure.repository_factory import (
    create_inspection_repository,
)

__all__ = [
    "DEFAULT_KOUTEI_FALLBACK",
    "InspectionService",
    "create_inspection_service",
]


class InspectionService(InspectionUseCase):
    """Backwards-compatible entry point used by the current UI."""

    def __init__(
        self, repository: InspectionRepository, export_directory: Path
    ) -> None:
        super().__init__(repository)
        self._export_directory = export_directory

    @property
    def export_directory(self) -> Path:
        return self._export_directory


def create_inspection_service() -> InspectionService:
    repository = create_inspection_repository()
    repo_db_path = getattr(repository, "db_path", "")
    default_export_dir = (
        Path(repo_db_path).resolve().parent
        if repo_db_path
        else get_application_base_dir()
    )
    export_dir = resolve_export_dir(default_export_dir)
    return InspectionService(repository, export_dir)
