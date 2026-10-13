"""Build the onefile Windows executable."""

from __future__ import annotations

import subprocess
import sys
import argparse
from pathlib import Path

from dotenv import dotenv_values, set_key


POSTGRES_ENV_KEYS = {
    "POSTGRES_CONNECTION_URL", "DATABASE_URL", "POSTGRES_DSN",
    "DELIVERY_LABEL_POSTGRES_CONNECTION_URL", "DELIVERY_LABEL_DATABASE_URL",
    "POSTGRES_SCHEMA", "EXPORT_DIR",
}


def prepare_bundled_env(root: Path, backend: str) -> Path | None:
    """Keep PostgreSQL settings without distributing Access-only settings."""
    source = root / ".env"
    if not source.is_file():
        return None
    if backend == "access":
        return source
    target = root / "build" / "postgres-config" / ".env"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("", encoding="utf-8")
    # Resolve references before dropping auxiliary variables such as DB_HOST.
    settings = dotenv_values(source)
    set_key(str(target), "DB_BACKEND", "postgres")
    for key in sorted(POSTGRES_ENV_KEYS):
        value = settings.get(key)
        if value is not None:
            set_key(str(target), key, value)
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", choices=("postgres", "access"), default="postgres")
    backend = parser.parse_args().backend
    root = Path(__file__).resolve().parent.parent
    py = root / ".venv" / "Scripts" / "python.exe"
    if not py.is_file():
        print("Error: .venv was not found.", file=sys.stderr)
        return 1

    png = root / "docs" / "app_icon.png"
    if not png.is_file():
        print(f"Error: PNG not found: {png}", file=sys.stderr)
        return 1
    arai_logo = root / "DESIGN" / "arai_logo.png"
    if not arai_logo.is_file():
        print(f"Error: Logo PNG not found: {arai_logo}", file=sys.stderr)
        return 1
    arai_logo_wt = root / "DESIGN" / "arai_logo_wt.png"

    def run(args: list[str | Path]) -> None:
        result = subprocess.run(
            [str(a) for a in args],
            cwd=str(root),
            check=False,
        )
        if result.returncode != 0:
            raise SystemExit(result.returncode)

    requirements = "requirements-access.txt" if backend == "access" else "requirements.txt"
    run([py, "-m", "pip", "install", "pyinstaller", "-r", requirements, "-q"])
    run([py, str(root / "scripts" / "generate_app_ico.py"), str(root)])

    ico = root / "build" / "app_icon.ico"
    if not ico.is_file():
        print(f"Error: ICO not found: {ico}", file=sys.stderr)
        return 1

    add_data = [
        "--add-data",
        f"{png};docs",
        # WinForms はウィンドウアイコンに .ico が必要（PNG は System.ArgumentException になる）
        "--add-data",
        f"{ico};docs",
        "--add-data",
        f"{root / 'src' / 'inspection_records_search' / 'web' / 'index.html'};src/inspection_records_search/web",
        # サイドバー用ロゴを実行ファイルに同梱する
        "--add-data",
        f"{arai_logo};DESIGN",
    ]
    if arai_logo_wt.is_file():
        add_data.extend(["--add-data", f"{arai_logo_wt};DESIGN"])

    marker = root / "build" / backend / "database_backend.txt"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(backend, encoding="utf-8")
    add_data.extend(["--add-data", f"{marker};."])

    env_path = prepare_bundled_env(root, backend)
    if env_path is not None:
        add_data.extend(["--add-data", f"{env_path};."])
        print(f"Bundling {backend} settings into the executable (values are not logged).")
    else:
        print(
            "Warning: .env not found, so it will not be bundled. "
            "For distribution, place .env next to the exe if needed."
        )

    exe_name = "外観検査記録照会"
    profile_args = ["--workpath", str(root / "build" / backend)]
    if backend == "postgres":
        for module in (
            "pyodbc", "pypyodbc", "win32com",
            "inspection_records_search.infrastructure.access_gateway",
        ):
            profile_args.extend(["--exclude-module", module])
    else:
        # Keep an Access-capable artifact separate from the production build.
        profile_args.extend([
            "--distpath", str(root / "dist" / "access"),
            "--specpath", str(root / "build" / "access"),
        ])
    cmd = [
        str(py),
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        exe_name,
        "--icon",
        str(ico),
        "--paths",
        "src",
        "--collect-all",
        "webview",
        # PyInstaller が動的 import を取りこぼす対策（参考: Gauge_Management の PinGaugeMgmt.spec）
        "--hidden-import",
        "webview.platforms.edgechromium",
        "--hidden-import",
        "webview.platforms.winforms",
        "--hidden-import",
        "webview.platforms.win32",
        "--exclude-module",
        "PySide6",
        "--exclude-module",
        "PyQt6",
        "--exclude-module",
        "PyQt5",
        "--exclude-module",
        "qtpy",
        *profile_args,
        *add_data,
        "main.py",
    ]
    run(cmd)
    dist_dir = root / "dist" if backend == "postgres" else root / "dist" / "access"
    dist = dist_dir / f"{exe_name}.exe"
    run([py, str(root / "scripts" / "verify_build.py"), str(dist), "--backend", backend])
    print(f"Built: {dist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
