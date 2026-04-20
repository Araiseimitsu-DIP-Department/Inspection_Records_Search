"""Generate a Windows ICO file from the docs PNG."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: generate_app_ico.py <repo_root>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    png = root / "docs" / "精密部品の品質検査.png"
    ico = root / "build" / "app_icon.ico"

    if not png.is_file():
        print(f"PNG not found: {png}", file=sys.stderr)
        return 1

    ico.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(png).convert("RGBA")
    width, height = img.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    img = img.crop((left, top, left + side, top + side))
    img.resize((256, 256), Image.Resampling.LANCZOS).save(ico, format="ICO")
    print(f"Created: {ico}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
