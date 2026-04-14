"""アプリ設定の読み込み（.env は exe / プロジェクト直下）。"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def get_application_base_dir() -> Path:
    """配布 exe 時は exe 所在フォルダ、開発時はリポジトリルート。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


def resource_path(*parts: str) -> Path:
    """PyInstaller onefile 時は展開先、開発時はリポジトリルート基準。"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).joinpath(*parts)
    return get_application_base_dir().joinpath(*parts)


def get_window_icon_png_path() -> Path | None:
    """ウィンドウ・タスクバー用アイコン。"""
    p = resource_path("docs", "精密部品の品質検査.png")
    if p.is_file():
        return p
    return None


def load_env() -> None:
    """バンドル内 .env を先に読み、exe 隣の .env で上書き可能。"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        bundled = Path(sys._MEIPASS) / ".env"
        if bundled.is_file():
            load_dotenv(bundled, override=False)
    env_path = get_application_base_dir() / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=True)


def get_access_db_path() -> str:
    """Access DB のフルパス（既定 backend 用）。"""
    load_env()
    return (os.getenv("ACCESS_DB_PATH") or "").strip().strip('"')


def get_database_backend() -> str:
    """使用する DB backend。既定は access。"""
    load_env()
    return (os.getenv("DATABASE_BACKEND") or "access").strip().lower()


def get_postgres_dsn() -> str:
    """将来の PostgreSQL 用 DSN / 接続文字列。"""
    load_env()
    return (os.getenv("POSTGRES_DSN") or "").strip().strip('"')


def get_export_dir() -> str:
    """Excel 出力先の明示指定。未指定なら backend ごとの既定値を使う。"""
    load_env()
    return (os.getenv("EXPORT_DIR") or "").strip().strip('"')


def validate_access_db_path(path: str) -> tuple[bool, str]:
    """存在確認（UNC パス可）。"""
    if not path:
        return False, "ACCESS_DB_PATH が .env に設定されていません。"
    p = Path(path)
    try:
        if not p.is_file():
            return False, f"データベースファイルが見つかりません:\n{path}"
    except OSError as e:
        return False, f"データベースファイルを確認できません:\n{path}\n{e}"
    if p.suffix.lower() not in (".accdb", ".mdb"):
        return False, ".accdb または .mdb を指定してください。"
    return True, ""


def validate_database_settings() -> tuple[bool, str]:
    backend = get_database_backend()
    if backend == "access":
        return validate_access_db_path(get_access_db_path())
    if backend == "postgres":
        dsn = get_postgres_dsn()
        if not dsn:
            return (
                False,
                "DATABASE_BACKEND=postgres の場合、POSTGRES_DSN を設定してください。",
            )
        return True, ""
    return False, f"DATABASE_BACKEND の値が不正です: {backend}"


def resolve_export_dir(default_dir: Path) -> Path:
    """EXPORT_DIR があればそれを使い、無ければ既定ディレクトリ。"""
    raw = get_export_dir()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else default_dir / p
    return default_dir
