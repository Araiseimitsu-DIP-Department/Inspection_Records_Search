"""Shared exception types and user-facing error messages."""

from __future__ import annotations


class AppError(Exception):
    """Base class for application-level errors."""


class ConfigurationError(AppError):
    """Raised when application settings are incomplete or invalid."""


class DatabaseError(AppError):
    """Base class for database-related failures."""


class DatabaseUnavailableError(DatabaseError):
    """Raised when the Access file or ODBC connection is not available."""


class DatabaseQueryError(DatabaseError):
    """Raised when a query fails for a generic ODBC reason."""


class DataIntegrityError(DatabaseError):
    """Raised when the database contains inconsistent or unexpected data."""


class DataConversionError(DatabaseError):
    """Raised when a field cannot be converted to the expected type."""


def describe_exception(exc: BaseException) -> str:
    """Return a friendly message suitable for a QMessageBox."""
    if isinstance(exc, DatabaseUnavailableError):
        return (
            "データベースに接続できません。\n"
            "NAS 接続、Access ファイルの存在、ODBC ドライバを確認してください。"
        )
    if isinstance(exc, DataConversionError):
        return (
            "データの型変換に失敗しました。\n"
            "Access 側の NULL 値や型不一致を確認してください。"
        )
    if isinstance(exc, DataIntegrityError):
        return (
            "データ不整合が検出されました。\n"
            "マスタ不備、欠損、想定外の値を確認してください。"
        )
    if isinstance(exc, DatabaseQueryError):
        return (
            "データベース処理に失敗しました。\n"
            "詳細はログを確認してください。"
        )
    if isinstance(exc, ConfigurationError):
        return str(exc) or "設定に問題があります。"
    text = str(exc).strip()
    return text or "処理に失敗しました。詳細はログを確認してください。"
