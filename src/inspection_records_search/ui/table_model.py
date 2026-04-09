"""QTableView 用テーブルモデル（列見出し・型に応じた寄せ）。"""

from __future__ import annotations

import datetime as dt
import re
from decimal import Decimal
from typing import Any, Optional

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

# Access 列名は「工程NO」のまま。画面上の列見出しのみ「工程No」に揃える。
_HEADER_LABEL_DISPLAY: dict[str, str] = {"工程NO": "工程No"}


def _normalize_header_labels(headers: list[str]) -> list[str]:
    return [_HEADER_LABEL_DISPLAY.get(h, h) for h in headers]


def _parse_loose_time_string(s: str) -> Optional[dt.time]:
    """DB や ODBC が返す時刻文字列を解釈（例: 8:40:00, 08:40）。"""
    s = s.strip()
    if not s:
        return None
    m = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?", s)
    if not m:
        return None
    try:
        return dt.time(int(m.group(1)), int(m.group(2)))
    except ValueError:
        return None


def _format_time_h_mm(val: Any) -> Optional[str]:
    """時刻列：先頭ゼロなしの H:mm（例: 8:40）。"""
    if val is None:
        return ""
    if isinstance(val, dt.datetime):
        t = val.time()
        return f"{t.hour}:{t.minute:02d}"
    if isinstance(val, dt.time):
        return f"{val.hour}:{val.minute:02d}"
    if isinstance(val, str):
        t = _parse_loose_time_string(val)
        if t is not None:
            return f"{t.hour}:{t.minute:02d}"
        return val.strip()
    return None


def _format_date_yyyy_mm_dd(val: Any) -> Optional[str]:
    """日付・日時の日付部分を yyyy/mm/dd で表示。"""
    if val is None:
        return ""
    if isinstance(val, dt.datetime):
        return val.strftime("%Y/%m/%d")
    if isinstance(val, dt.date):
        return val.strftime("%Y/%m/%d")
    return None


def _format_display_cell(header: str, val: Any) -> str:
    """セル表示文字列（日付は yyyy/mm/dd、時刻列は H:mm）。"""
    if val is None:
        return ""

    if header == "時刻":
        out = _format_time_h_mm(val)
        if out is not None:
            return out
        return str(val)

    dt_out = _format_date_yyyy_mm_dd(val)
    if dt_out is not None:
        return dt_out

    if isinstance(val, Decimal):
        return str(val)
    if isinstance(val, bytes):
        return val.decode(errors="replace")
    return str(val)


def _header_suggests_right(header: str) -> bool:
    """数値系・時間系の列見出し（参考リストの右寄せ列に合わせる）。"""
    if not header:
        return False
    keys = (
        "数量",
        "作業時間",
        "不良率",
        "件数",
        "合計",
        "総不具合",
        "不具合数",
        "外観キズ",
        "圧痕",
        "切粉",
        "割れ",
        "穴大",
    )
    for k in keys:
        if k in header:
            return True
    if header.endswith("率") and len(header) <= 12:
        return True
    return False


def _header_suggests_left(header: str) -> bool:
    """ID・名称・日付など左寄せが自然な列。"""
    if not header:
        return True
    keys = (
        "品番",
        "品名",
        "検査員",
        "客先",
        "生産ロット",
        "ロット",
        "工程No",
        "号機",
        "指示日",
        "日付",
        "フラグ",
    )
    for k in keys:
        if k in header:
            return True
    if "名" in header and "数量" not in header:
        return True
    if header.endswith("ID") or header == "ID":
        return True
    return False


def _cell_alignment(header: str, value: Any) -> Qt.AlignmentFlag:
    if header == "時刻":
        return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
    if _header_suggests_right(header):
        return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    if _header_suggests_left(header):
        return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
    if isinstance(value, (int, float, Decimal)):
        return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
    return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


def _header_alignment(_header: str) -> Qt.AlignmentFlag:
    """全リストの列見出しは中央。"""
    return Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter


class RowTableModel(QAbstractTableModel):
    def __init__(
        self,
        headers: list[str],
        rows: list[tuple],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._headers = list(headers)
        self._rows = [list(r) for r in rows]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if not index.isValid():
            return None
        col = index.column()
        row = index.row()
        if col >= len(self._headers) or row >= len(self._rows):
            return None
        cell_row = self._rows[row]
        val = cell_row[col] if col < len(cell_row) else None
        h = self._headers[col]

        if role == Qt.ItemDataRole.DisplayRole:
            return _format_display_cell(h, val)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return _cell_alignment(h, val)
        return None

    def headerData(  # noqa: N802
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if orientation == Qt.Orientation.Horizontal and section < len(
            self._headers
        ):
            h = self._headers[section]
            if role == Qt.ItemDataRole.DisplayRole:
                return h
            if role == Qt.ItemDataRole.TextAlignmentRole:
                return _header_alignment(h)
            return None
        if orientation == Qt.Orientation.Horizontal:
            return None
        return super().headerData(section, orientation, role)

    def set_data(self, headers: list[str], rows: list[tuple]) -> None:
        self.beginResetModel()
        self._headers = _normalize_header_labels(list(headers))
        self._rows = [list(r) for r in rows]
        self.endResetModel()

    def raw_rows(self) -> list[tuple]:
        """Excel 出力用（DB 生値）。"""
        return [tuple(r) for r in self._rows]

    def headers(self) -> list[str]:
        return list(self._headers)


def column_index(headers: list[str], *names: str) -> Optional[int]:
    """最初に一致した列番号。"""
    lower = [h.lower() for h in headers]
    for name in names:
        key = name.lower()
        try:
            return lower.index(key)
        except ValueError:
            continue
    return None
