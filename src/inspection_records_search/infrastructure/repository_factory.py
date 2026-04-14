"""Repository selection for the current DB backend."""

from __future__ import annotations

from inspection_records_search.config import (
    get_access_db_path,
    get_database_backend,
    get_postgres_dsn,
    validate_access_db_path,
)
from inspection_records_search.infrastructure.access_gateway import (
    AccessInspectionRepository,
)
from inspection_records_search.infrastructure.postgres_repository import (
    PostgresInspectionRepository,
)
from inspection_records_search.domain.repositories import InspectionRepository
from inspection_records_search.shared.errors import ConfigurationError


def create_inspection_repository() -> InspectionRepository:
    backend = get_database_backend()
    if backend == "access":
        db_path = get_access_db_path()
        ok, msg = validate_access_db_path(db_path)
        if not ok:
            raise ConfigurationError(msg)
        return AccessInspectionRepository(db_path)
    if backend == "postgres":
        dsn = get_postgres_dsn()
        if not dsn:
            raise ConfigurationError(
                "DATABASE_BACKEND=postgres の場合、POSTGRES_DSN を設定してください。"
            )
        return PostgresInspectionRepository(dsn)
    raise ConfigurationError(f"DATABASE_BACKEND の値が不正です: {backend}")
