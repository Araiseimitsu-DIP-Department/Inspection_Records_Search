"""Excel 出力ボタン用アイコン（緑地・白い表イメージの SVG）。"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# 参考：角丸緑・白ドキュメント・右上折り返し・行を示す横線
_EXCEL_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#217346"/>
  <path fill="#ffffff" d="M18 14h20L42 18l10 10v28H18V14z"/>
  <path fill="#c8e6d0" d="M38 14h4l10 10H38V14z"/>
  <rect x="24" y="34" width="22" height="3.2" rx="1" fill="#217346"/>
  <rect x="24" y="40" width="22" height="3.2" rx="1" fill="#217346"/>
  <rect x="24" y="46" width="17" height="3.2" rx="1" fill="#217346"/>
</svg>"""


def excel_export_icon(size: int = 18) -> QIcon:
    """QPushButton 用 QIcon（複解像度用に複数サイズ生成）。"""
    renderer = QSvgRenderer(QByteArray(_EXCEL_SVG))
    icon = QIcon()
    for px in (size, int(size * 1.5)):
        pm = QPixmap(px, px)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        renderer.render(p)
        p.end()
        icon.addPixmap(pm)
    return icon


def apply_excel_button_icon(button, icon_size: int = 18) -> None:
    """Excel 出力ボタンにアイコンを付与（テキスト左）。"""
    button.setIcon(excel_export_icon(icon_size))
    button.setIconSize(QSize(icon_size, icon_size))
