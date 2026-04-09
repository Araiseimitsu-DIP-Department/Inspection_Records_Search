"""PyInstaller 用：docs の PNG から exe アイコン ICO を生成（build_exe.ps1 から呼び出し）。"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    if len(sys.argv) < 2:
        print("使い方: generate_app_ico.py <リポジトリルート>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    png = root / "docs" / "精密部品の品質検査.png"
    ico = root / "build" / "app_icon.ico"
    if not png.is_file():
        print(f"PNG が見つかりません: {png}", file=sys.stderr)
        return 1
    ico.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(png).convert("RGBA")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    r256 = img.resize((256, 256), Image.Resampling.LANCZOS)
    r256.save(ico, format="ICO")
    print(f"生成: {ico}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
