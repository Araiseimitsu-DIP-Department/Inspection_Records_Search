"""onefile exe ビルド（PyInstaller）。日本語パス対策で Python から起動する。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    py = root / ".venv" / "Scripts" / "python.exe"
    if not py.is_file():
        print("エラー: .venv が見つかりません。", file=sys.stderr)
        return 1

    png = root / "docs" / "精密部品の品質検査.png"
    if not png.is_file():
        print(f"エラー: PNG がありません: {png}", file=sys.stderr)
        return 1

    def run(args: list[str | Path]) -> None:
        r = subprocess.run(
            [str(a) for a in args],
            cwd=str(root),
            check=False,
        )
        if r.returncode != 0:
            raise SystemExit(r.returncode)

    run([py, "-m", "pip", "install", "pyinstaller", "pillow", "-q"])
    run([py, str(root / "scripts" / "generate_app_ico.py"), str(root)])

    ico = root / "build" / "app_icon.ico"
    if not ico.is_file():
        print(f"エラー: ICO がありません: {ico}", file=sys.stderr)
        return 1

    add_data = [
        "--add-data",
        f"{png};docs",
    ]
    env_path = root / ".env"
    if env_path.is_file():
        add_data.extend(["--add-data", f"{env_path};."])
        print(".env をバンドルに含めます。")
    else:
        print(
            "警告: .env が無いためバンドルしません。"
            "配布時は exe と同じフォルダに .env を置けます。"
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
        "--hidden-import",
        "PySide6.QtCore",
        "--hidden-import",
        "PySide6.QtGui",
        "--hidden-import",
        "PySide6.QtWidgets",
        "--hidden-import",
        "PySide6.QtSvg",
        "--hidden-import",
        "pyodbc",
        "--hidden-import",
        "dotenv",
        *add_data,
        "main.py",
    ]
    run(cmd)
    dist = root / "dist" / f"{exe_name}.exe"
    print(f"完了: {dist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
