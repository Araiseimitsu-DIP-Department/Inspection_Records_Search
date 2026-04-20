"""Build the onefile Windows executable."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    py = root / ".venv" / "Scripts" / "python.exe"
    if not py.is_file():
        print("Error: .venv was not found.", file=sys.stderr)
        return 1

    png = root / "docs" / "精密部品の品質検査.png"
    if not png.is_file():
        print(f"Error: PNG not found: {png}", file=sys.stderr)
        return 1

    def run(args: list[str | Path]) -> None:
        result = subprocess.run(
            [str(a) for a in args],
            cwd=str(root),
            check=False,
        )
        if result.returncode != 0:
            raise SystemExit(result.returncode)

    run([py, "-m", "pip", "install", "pyinstaller", "-r", "requirements.txt", "-q"])
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
    ]

    env_path = root / ".env"
    if env_path.is_file():
        add_data.extend(["--add-data", f"{env_path};."])
        print("Bundling .env into the executable.")
    else:
        print(
            "Warning: .env not found, so it will not be bundled. "
            "For distribution, place .env next to the exe if needed."
        )

    exe_name = "外観検査記録照会"
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
        *add_data,
        "main.py",
    ]
    run(cmd)
    dist = root / "dist" / f"{exe_name}.exe"
    print(f"Built: {dist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
