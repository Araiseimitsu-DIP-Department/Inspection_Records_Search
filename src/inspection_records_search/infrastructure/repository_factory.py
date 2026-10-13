"""Repository selection for the current DB backend."""

from __future__ import annotations

from inspection_records_search.config import (
    get_access_db_path,
    get_database_backend,
    get_delivery_label_postgres_dsn,
    get_postgres_dsn,
    validate_access_db_path,
    validate_build_backend,
)
from inspection_records_search.infrastructure.postgres_repository import (
    PostgresInspectionRepository,
)
from inspection_records_search.domain.repositories import InspectionRepository
from inspection_records_search.shared.errors import ConfigurationError


def create_inspection_repository() -> InspectionRepository:
    backend = get_database_backend()
    ok, msg = validate_build_backend(backend)
    if not ok:
        raise ConfigurationError(msg)
    if backend == "access":
        db_path = get_access_db_path()
        ok, msg = validate_access_db_path(db_path)
        if not ok:
            raise ConfigurationError(msg)
        try:
            from inspection_records_search.infrastructure.access_gateway import (
                AccessInspectionRepository,
            )
        except ImportError as exc:
            raise ConfigurationError(
                "Access接続には requirements-access.txt の導入とAccess対応ビルドが必要です。"
            ) from exc
        return AccessInspectionRepository(db_path)
    if backend == "postgres":
        dsn = get_postgres_dsn()
        if not dsn:
            raise ConfigurationError(
                "DB_BACKEND=postgres の場合、POSTGRES_CONNECTION_URL を設定してください。"
            )
        return PostgresInspectionRepository(dsn, get_delivery_label_postgres_dsn())
    raise ConfigurationError(f"DB_BACKEND の値が不正です: {backend}")
