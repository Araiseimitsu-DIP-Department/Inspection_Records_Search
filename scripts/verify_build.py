"""Inspect the actual PyInstaller executable without launching or extracting it."""
from __future__ import annotations

import argparse
from io import StringIO
from pathlib import Path

from dotenv import dotenv_values
from PyInstaller.archive.readers import CArchiveReader


def verify_build(path: Path, backend: str) -> dict[str, int | str]:
    archive = CArchiveReader(str(path))
    modules = archive.open_embedded_archive("PYZ.pyz").toc
    names = set(archive.toc)
    normalized = {n.replace("\\", "/").lower() for n in names}
    required_files = {
        "database_backend.txt", "docs/app_icon.png", "docs/app_icon.ico",
        "design/arai_logo.png", "src/inspection_records_search/web/index.html",
    }
    missing = required_files - normalized
    for module in ("psycopg", "psycopg_binary", "webview", "clr", "openpyxl", "dotenv"):
        if module not in modules:
            missing.add(module)
    if missing:
        raise RuntimeError(f"Missing required runtime components: {sorted(missing)}")
    if archive.extract("database_backend.txt").decode("utf-8").strip() != backend:
        raise RuntimeError("Backend marker does not match the requested build")
    if backend == "postgres":
        forbidden = [n for n in modules if n == "inspection_records_search.infrastructure.access_gateway"
                     or n.split(".")[0] in {"pyodbc", "pypyodbc", "win32com"}]
        forbidden.extend(n for n in names if any(
            token in n.lower() for token in ("pyodbc", "pypyodbc", "win32com", "aceodbc", "msaccess")
        ) or n.lower().endswith((".accdb", ".mdb", ".laccdb", ".ldb"))
            or n.replace("\\", "/").lower().startswith(("tests/", "scripts/", "database/")))
        if forbidden:
            raise RuntimeError(f"Access-only or development files were bundled: {sorted(forbidden)}")
        if ".env" in names:
            settings = dotenv_values(stream=StringIO(archive.extract(".env").decode("utf-8")))
            if "ACCESS_DB_PATH" in settings or settings.get("DB_BACKEND") != "postgres":
                raise RuntimeError("Bundled settings contain Access configuration")
    elif "inspection_records_search.infrastructure.access_gateway" not in modules or not any(
        "pyodbc" in n.lower() for n in names
    ):
        raise RuntimeError("Access build does not include Access runtime components")
    return {"backend": backend, "bytes": path.stat().st_size,
            "files": len(names), "modules": len(modules)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--backend", choices=("postgres", "access"), default="postgres")
    args = parser.parse_args()
    print("Build archive verification: PASS", verify_build(args.executable, args.backend))


if __name__ == "__main__":
    main()
