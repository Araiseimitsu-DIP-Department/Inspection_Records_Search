"""Application settings and resource path helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def get_application_base_dir() -> Path:
    """Return the application base directory.

    In a frozen executable this is the folder containing the exe.
    During development this is the project root.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def resource_path(*parts: str) -> Path:
    """Return a path that works both in development and in a frozen app."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).joinpath(*parts)
    return get_application_base_dir().joinpath(*parts)


def get_window_icon_png_path() -> Path | None:
    """Return the PNG used for the window and taskbar icon."""
    path = resource_path("docs", "精密部品の品質検査.png")
    return path if path.is_file() else None


def get_webview_window_icon_path() -> Path | None:
    """pywebview（WinForms / Edge WebView2）向けのアイコンパス。

    WinForms の System.Drawing.Icon は .ico のみ対応のため、同梱の app_icon.ico を優先する。
    """
    bundled = resource_path("docs", "app_icon.ico")
    if bundled.is_file():
        return bundled
    if not getattr(sys, "frozen", False):
        dev_ico = get_application_base_dir() / "build" / "app_icon.ico"
        if dev_ico.is_file():
            return dev_ico
    return get_window_icon_png_path()


def get_web_index_html_path() -> Path:
    """Return the bundled frontend entry point."""
    return resource_path("src", "inspection_records_search", "web", "index.html")


def load_env() -> None:
    """Load .env from both the bundled app and the current working tree."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled = Path(sys._MEIPASS) / ".env"
        if bundled.is_file():
            load_dotenv(bundled, override=False)

    env_path = get_application_base_dir() / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=True)


def get_access_db_path() -> str:
    """Return the Access database path from .env."""
    load_env()
    return (os.getenv("ACCESS_DB_PATH") or "").strip().strip('"')


def get_database_backend() -> str:
    """Return the configured database backend."""
    load_env()
    return (os.getenv("DATABASE_BACKEND") or "access").strip().lower()


def get_postgres_dsn() -> str:
    """Return the PostgreSQL DSN from .env."""
    load_env()
    return (os.getenv("POSTGRES_DSN") or "").strip().strip('"')


def get_export_dir() -> str:
    """Return the Excel export directory from .env."""
    load_env()
    return (os.getenv("EXPORT_DIR") or "").strip().strip('"')


def validate_access_db_path(path: str) -> tuple[bool, str]:
    """Validate the Access database path."""
    if not path:
        return False, "ACCESS_DB_PATH is not set in .env."

    p = Path(path)
    try:
        if not p.is_file():
            return False, f"Database file not found:\n{path}"
    except OSError as exc:
        return False, f"Could not inspect the database file:\n{path}\n{exc}"

    if p.suffix.lower() not in (".accdb", ".mdb"):
        return False, "Please specify a .accdb or .mdb file."

    return True, ""


def validate_database_settings() -> tuple[bool, str]:
    """Validate the configured database connection settings."""
    backend = get_database_backend()
    if backend == "access":
        return validate_access_db_path(get_access_db_path())
    if backend == "postgres":
        dsn = get_postgres_dsn()
        if not dsn:
            return False, "Set POSTGRES_DSN when DATABASE_BACKEND=postgres."
        return True, ""
    return False, f"Invalid DATABASE_BACKEND value: {backend}"


def resolve_export_dir(default_dir: Path) -> Path:
    """Return the export directory or a fallback directory."""
    raw = get_export_dir()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else default_dir / path
    return default_dir
