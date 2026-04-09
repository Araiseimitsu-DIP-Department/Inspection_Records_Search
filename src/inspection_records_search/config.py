"""アプリ設定の読み込み（.env は exe / プロジェクト直下）。"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
import os


def get_application_base_dir() -> Path:
    """配布 exe 時は exe 所在フォルダ、開発時はリポジトリルート。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # src/inspection_records_search/config.py -> リポジトリルート
    return Path(__file__).resolve().parent.parent.parent


def resource_path(*parts: str) -> Path:
    """PyInstaller onefile 時は展開先（_MEIPASS）、開発時はリポジトリルート基準のパス。"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).joinpath(*parts)
    return get_application_base_dir().joinpath(*parts)


def get_window_icon_png_path() -> Path | None:
    """ウィンドウ・タスクバー用アイコン（docs 配下 PNG）。"""
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
    """親 .accdb のフルパス（必須）。"""
    load_env()
    path = (os.getenv("ACCESS_DB_PATH") or "").strip().strip('"')
    return path


def validate_access_db_path(path: str) -> tuple[bool, str]:
    """存在確認（UNC パス可）。"""
    if not path:
        return False, "ACCESS_DB_PATH が .env に設定されていません。"
    p = Path(path)
    if not p.is_file():
        return False, f"データベースファイルが見つかりません:\n{path}"
    if p.suffix.lower() not in (".accdb", ".mdb"):
        return False, ".accdb または .mdb を指定してください。"
    return True, ""
