"""Process names and matching shared by both database backends."""

from __future__ import annotations

DEFAULT_KOUTEI_FALLBACK: tuple[str, ...] = (
    "バリ取り",
    "ゲージ検査",
    "エアー吹き",
    "切粉除去",
    "返品再検査",
    "マイクロ検",
    "仕掛再検査",
    "ボッチ取り",
    "在庫再検査",
    "トレー詰め",
)

_KOUTEI_CODE_NAME: tuple[tuple[str, str], ...] = (
    ("15", "バリ取り"),
    ("16", "ゲージ検査"),
    ("17", "エアー吹き"),
    ("18", "切粉除去"),
    ("19", "返品再検査"),
    ("20", "マイクロ検"),
    ("21", "仕掛再検査"),
    ("22", "ボッチ取り"),
    ("23", "在庫再検査"),
    ("24", "トレー詰め"),
)


def _expand_koutei_match_values(raw: str) -> list[str]:
    """工程NO 条件に、コードと名称の両方を含める。"""
    t = raw.strip()
    if not t:
        return []
    out: list[str] = []
    seen: set[str] = set()

    def add(v: str) -> None:
        if v and v not in seen:
            seen.add(v)
            out.append(v)

    add(t)
    for code, name in _KOUTEI_CODE_NAME:
        if t == code:
            add(name)
        elif t == name:
            add(code)
    return out
