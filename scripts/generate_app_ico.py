"""docs/app_icon.png から Windows 用 ICO を生成する。"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def _make_near_black_transparent(img: Image.Image, threshold: int = 30) -> Image.Image:
    """黒背景を透過にしてタスクバー等で自然に見えるようにする。"""
    rgba = img.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if r <= threshold and g <= threshold and b <= threshold:
                pixels[x, y] = (r, g, b, 0)
    return rgba


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: generate_app_ico.py <repo_root>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    png = root / "docs" / "app_icon.png"
    ico = root / "build" / "app_icon.ico"

    if not png.is_file():
        print(f"PNG not found: {png}", file=sys.stderr)
        return 1

    ico.parent.mkdir(parents=True, exist_ok=True)
    img = _make_near_black_transparent(Image.open(png))
    width, height = img.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    img = img.crop((left, top, left + side, top + side))
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.resize((256, 256), Image.Resampling.LANCZOS).save(
        ico,
        format="ICO",
        sizes=icon_sizes,
    )
    print(f"Created: {ico}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
