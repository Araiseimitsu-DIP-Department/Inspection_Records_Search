"""ピンゲージ管理画面を参考にしたコーポレート系 QSS（PySide6）。"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QAbstractItemView, QApplication

# 参考画像トークン
PAGE_BG = "#F5F7F9"
SIDEBAR_BG = "#FFFFFF"
PRIMARY = "#004BB1"
PRIMARY_HOVER = "#003A8C"
ON_PRIMARY = "#FFFFFF"
TEXT_MAIN = "#1a1f26"
TEXT_MUTED = "#5c6570"
INPUT_BG = "#E0E4E9"
CARD_BG = "#FFFFFF"
BORDER_SUBTLE = "#E2E8F0"
# 一覧テーブル（外観検査リスト参考）
TABLE_HEADER_BG = "#E9F0F5"
TABLE_ROW_BASE = "#FFFFFF"
TABLE_ROW_ALT = "#F0F4F8"
TABLE_GRIDLINE = "#E8ECEF"
TABLE_SEL_BG = "rgba(0, 75, 177, 0.12)"


def apply_standard_table_view(view) -> None:
    """全データ一覧で共通の見た目（角丸・ゼブラ・非表示グリッド等）。"""
    from PySide6.QtWidgets import QTableView

    if not isinstance(view, QTableView):
        return
    view.setObjectName("dataTable")
    view.setShowGrid(False)
    view.setWordWrap(False)
    view.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    view.verticalHeader().setVisible(False)
    view.horizontalHeader().setStretchLastSection(True)
    view.horizontalHeader().setDefaultAlignment(
        Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
    )
    view.horizontalHeader().setMinimumHeight(40)
    view.verticalHeader().setDefaultSectionSize(40)

    model = view.model()
    if model is not None:

        def _defer_resize_columns() -> None:
            # 列非表示など同一処理内の後続処理の後に幅を計算する
            QTimer.singleShot(0, view.resizeColumnsToContents)

        model.modelReset.connect(_defer_resize_columns)


def apply_app_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(PAGE_BG))
    pal.setColor(QPalette.ColorRole.Base, QColor(CARD_BG))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(PAGE_BG))
    pal.setColor(QPalette.ColorRole.Button, QColor(INPUT_BG))
    pal.setColor(QPalette.ColorRole.Text, QColor(TEXT_MAIN))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_MAIN))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT_MAIN))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(PRIMARY))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(ON_PRIMARY))
    app.setPalette(pal)

    app.setStyleSheet(
        f"""
        QWidget#appRoot {{
            background-color: {PAGE_BG};
            font-size: 13px;
            color: {TEXT_MAIN};
        }}
        QFrame#sidebar {{
            background-color: {SIDEBAR_BG};
            border: none;
            border-right: 1px solid {BORDER_SUBTLE};
            min-width: 220px;
            max-width: 260px;
        }}
        /* タイトルフォントサイズは main_window でサイドバー幅に合わせて設定 */
        QLabel#sidebarAppTitle {{
            color: {PRIMARY};
            padding: 4px 6px 2px 12px;
        }}
        QLabel#sidebarTagline {{
            color: {TEXT_MUTED};
            font-size: 11px;
            padding: 0 6px 8px 12px;
        }}
        /* 左ナビ：アクティブ時は左に青バー＋文字色 */
        QPushButton#sidebarNav {{
            text-align: left;
            padding: 12px 16px 12px 20px;
            margin: 2px 0 2px 0;
            border: none;
            border-radius: 0;
            background: transparent;
            color: {TEXT_MAIN};
            font-size: 14px;
            font-weight: 500;
        }}
        QPushButton#sidebarNav:hover {{
            background-color: rgba(0, 75, 177, 0.06);
        }}
        QPushButton#sidebarNav:checked {{
            color: {PRIMARY};
            font-weight: 700;
            border-left: 4px solid {PRIMARY};
            padding-left: 16px;
            background-color: rgba(0, 75, 177, 0.06);
        }}
        QWidget#contentShell {{
            background-color: {PAGE_BG};
            border: none;
        }}
        QFrame#contentCard {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER_SUBTLE};
            border-radius: 18px;
        }}
        QLabel#screenTitle {{
            color: {PRIMARY};
            font-size: 22px;
            font-weight: 800;
        }}
        QLabel#screenSubtitle {{
            color: {TEXT_MUTED};
            font-size: 13px;
            font-weight: 500;
            padding-left: 10px;
        }}
        QLabel#sectionLabel {{
            color: {TEXT_MAIN};
            font-size: 13px;
            font-weight: 700;
            padding: 8px 0 4px 0;
        }}
        QLabel#formLabel {{
            color: {TEXT_MAIN};
            font-weight: 500;
        }}
        QLabel#kouteiLegend {{
            color: {TEXT_MAIN};
            font-size: 11px;
            font-weight: 500;
            padding: 4px 2px;
            background: transparent;
        }}
        /* 個人別：工程No 凡例（1行・幅不足時のみ横スクロール） */
        QScrollArea#kouteiLegendScroll {{
            background-color: rgba(255, 255, 255, 0.65);
            border: 1px solid {BORDER_SUBTLE};
            border-radius: 10px;
        }}
        QScrollArea#kouteiLegendScroll QWidget {{
            background: transparent;
        }}
        QScrollArea#kouteiLegendScroll QScrollBar:horizontal {{
            background: transparent;
            height: 8px;
            margin: 0 6px 4px 6px;
            border-radius: 4px;
        }}
        QScrollArea#kouteiLegendScroll QScrollBar::handle:horizontal {{
            background: rgba(0, 75, 177, 0.28);
            min-width: 24px;
            border-radius: 4px;
        }}
        QScrollArea#kouteiLegendScroll QScrollBar::handle:horizontal:hover {{
            background: rgba(0, 75, 177, 0.42);
        }}
        QScrollArea#kouteiLegendScroll QScrollBar::add-line:horizontal,
        QScrollArea#kouteiLegendScroll QScrollBar::sub-line:horizontal {{
            width: 0;
            height: 0;
        }}
        QGroupBox {{
            font-size: 14px;
            font-weight: 700;
            color: {TEXT_MAIN};
            border: none;
            margin-top: 12px;
            padding-top: 8px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 0;
            padding: 0 0 8px 0;
        }}
        QLineEdit, QComboBox, QDateEdit {{
            background-color: {INPUT_BG};
            border: none;
            border-radius: 9px;
            padding: 8px 12px;
            min-height: 20px;
            color: {TEXT_MAIN};
        }}
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
            border: 2px solid rgba(0, 75, 177, 0.35);
            padding: 6px 10px;
        }}
        QComboBox::drop-down {{
            border: none;
            width: 32px;
            background: transparent;
        }}
        /* 検査員コンボ：閉じた状態を LineEdit と同系に */
        QComboBox#inspectorCombo {{
            combobox-popup: 0;
            background-color: {INPUT_BG};
            border: none;
            border-radius: 9px;
            padding: 8px 12px;
            padding-right: 28px;
            min-height: 22px;
            color: {TEXT_MAIN};
        }}
        QComboBox#inspectorCombo:hover {{
            background-color: #d8dde4;
        }}
        QComboBox#inspectorCombo:focus {{
            border: 2px solid rgba(0, 75, 177, 0.35);
            padding: 6px 10px;
            padding-right: 26px;
        }}
        /* 三角なし。右端は一覧表示用の無地クリック領域のみ */
        QComboBox#inspectorCombo::drop-down {{
            border: none;
            width: 24px;
            background: transparent;
            subcontrol-origin: padding;
            subcontrol-position: center right;
        }}
        QComboBox#inspectorCombo::down-arrow {{
            image: none;
            border: none;
            width: 0;
            height: 0;
        }}
        QComboBox#inspectorCombo QLineEdit {{
            border: none;
            background: transparent;
            padding: 0;
            min-height: 22px;
            color: {TEXT_MAIN};
        }}
        /* 検査員プルダウン一覧：カード風・縦長抑制は inspector_combo でコード調整 */
        QComboBox#inspectorCombo QAbstractItemView {{
            border: 1px solid {BORDER_SUBTLE};
            border-radius: 10px;
            background-color: {CARD_BG};
            padding: 6px;
            outline: none;
            font-size: 13px;
            color: {TEXT_MAIN};
            min-height: 0;
            selection-background-color: {TABLE_SEL_BG};
            selection-color: {TEXT_MAIN};
        }}
        QComboBox#inspectorCombo QAbstractItemView::item {{
            padding: 8px 12px;
            min-height: 32px;
            border: none;
            border-radius: 6px;
        }}
        QComboBox#inspectorCombo QAbstractItemView::item:selected {{
            background-color: rgba(0, 75, 177, 0.16);
            color: {TEXT_MAIN};
        }}
        QComboBox#inspectorCombo QAbstractItemView::item:hover {{
            background-color: rgba(0, 75, 177, 0.09);
        }}
        QComboBox#inspectorCombo QAbstractItemView QScrollBar:vertical {{
            width: 10px;
            margin: 4px 2px 4px 0;
            background: {PAGE_BG};
            border-radius: 5px;
            border: none;
        }}
        QComboBox#inspectorCombo QAbstractItemView QScrollBar::handle:vertical {{
            background: #c5ced8;
            min-height: 28px;
            border-radius: 5px;
        }}
        QComboBox#inspectorCombo QAbstractItemView QScrollBar::handle:vertical:hover {{
            background: #aab6c3;
        }}
        QComboBox#inspectorCombo QAbstractItemView QScrollBar::add-line:vertical,
        QComboBox#inspectorCombo QAbstractItemView QScrollBar::sub-line:vertical {{
            width: 0;
            height: 0;
        }}
        /* 入力時の絞り込み候補ポップアップ（QCompleter） */
        QListView#inspectorCompleterPopup {{
            border: 1px solid {BORDER_SUBTLE};
            border-radius: 10px;
            background-color: {CARD_BG};
            padding: 6px;
            outline: none;
            font-size: 13px;
            color: {TEXT_MAIN};
            min-height: 0;
        }}
        QListView#inspectorCompleterPopup::item {{
            padding: 8px 12px;
            min-height: 32px;
            border-radius: 6px;
        }}
        QListView#inspectorCompleterPopup::item:selected {{
            background-color: rgba(0, 75, 177, 0.16);
            color: {TEXT_MAIN};
        }}
        QListView#inspectorCompleterPopup::item:hover {{
            background-color: rgba(0, 75, 177, 0.09);
        }}
        QListView#inspectorCompleterPopup QScrollBar:vertical {{
            width: 10px;
            margin: 4px 2px 4px 0;
            background: {PAGE_BG};
            border-radius: 5px;
            border: none;
        }}
        QListView#inspectorCompleterPopup QScrollBar::handle:vertical {{
            background: #c5ced8;
            min-height: 28px;
            border-radius: 5px;
        }}
        QCheckBox {{
            color: {TEXT_MUTED};
            spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 1px solid {BORDER_SUBTLE};
            background: {INPUT_BG};
        }}
        QCheckBox::indicator:checked {{
            background: {PRIMARY};
            border-color: {PRIMARY};
        }}
        /* 高さは QLineEdit 等（padding 8px・角丸 9px）に合わせる */
        QPushButton#primaryButton {{
            background-color: {PRIMARY};
            color: {ON_PRIMARY};
            font-weight: 700;
            font-size: 13px;
            border: none;
            border-radius: 9px;
            padding: 8px 16px;
            min-width: 72px;
        }}
        QPushButton#primaryButton:hover {{
            background-color: {PRIMARY_HOVER};
        }}
        QPushButton#primaryButton:pressed {{
            background-color: #002f75;
        }}
        /* 枠線 1px 分、上下 padding を primary より 1px 狭くして外観の高さを揃える */
        QPushButton#outlineButton {{
            background-color: {CARD_BG};
            color: {PRIMARY};
            font-weight: 600;
            font-size: 13px;
            border: 1px solid {PRIMARY};
            border-radius: 9px;
            padding: 7px 14px;
        }}
        QPushButton#outlineButton:hover {{
            background-color: rgba(0, 75, 177, 0.08);
        }}
        /* デフォルトの QTableView（未使用想定） */
        QTableView {{
            background-color: {TABLE_ROW_BASE};
            alternate-background-color: {TABLE_ROW_ALT};
            border: 1px solid {BORDER_SUBTLE};
            border-radius: 10px;
            gridline-color: transparent;
        }}
        /* データ一覧：ヘッダー水色・ゼブラ・横罫線のみイメージ */
        QTableView#dataTable {{
            background-color: {TABLE_ROW_BASE};
            alternate-background-color: {TABLE_ROW_ALT};
            border: 1px solid {BORDER_SUBTLE};
            border-radius: 10px;
            gridline-color: transparent;
            font-size: 13px;
            selection-background-color: {TABLE_SEL_BG};
            selection-color: {TEXT_MAIN};
        }}
        QTableView#dataTable::item {{
            padding: 8px 12px;
            border: none;
            border-bottom: 1px solid {TABLE_GRIDLINE};
        }}
        QTableView#dataTable::item:selected {{
            background-color: {TABLE_SEL_BG};
            color: {TEXT_MAIN};
        }}
        QTableView#dataTable::item:alternate {{
            border-bottom: 1px solid {TABLE_GRIDLINE};
        }}
        QHeaderView {{
            background-color: transparent;
        }}
        QTableView#dataTable QHeaderView::section {{
            background-color: {TABLE_HEADER_BG};
            color: {TEXT_MAIN};
            padding: 11px 12px;
            border: none;
            border-right: 1px solid rgba(0, 0, 0, 0.04);
            border-bottom: 1px solid {BORDER_SUBTLE};
            font-weight: 700;
            font-size: 12px;
            text-align: center;
        }}
        QTableView#dataTable QHeaderView::section:first {{
            border-top-left-radius: 9px;
        }}
        QTableView#dataTable QHeaderView::section:last {{
            border-top-right-radius: 9px;
            border-right: none;
        }}
        QTableView#dataTable QScrollBar:vertical {{
            width: 11px;
            margin: 2px 2px 2px 0;
            background: {PAGE_BG};
            border-radius: 5px;
            border: none;
        }}
        QTableView#dataTable QScrollBar::handle:vertical {{
            background: #c5ced8;
            min-height: 36px;
            border-radius: 5px;
        }}
        QTableView#dataTable QScrollBar::handle:vertical:hover {{
            background: #aab6c3;
        }}
        QTableView#dataTable QScrollBar:horizontal {{
            height: 11px;
            margin: 0 2px 2px 2px;
            background: {PAGE_BG};
            border-radius: 5px;
            border: none;
        }}
        QTableView#dataTable QScrollBar::handle:horizontal {{
            background: #c5ced8;
            min-width: 36px;
            border-radius: 5px;
        }}
        QTableView#dataTable QScrollBar::handle:horizontal:hover {{
            background: #aab6c3;
        }}
        QTableView#dataTable QScrollBar::add-line, QTableView#dataTable QScrollBar::sub-line {{
            width: 0;
            height: 0;
        }}
        QSplitter::handle:horizontal {{
            width: 5px;
            background: {PAGE_BG};
        }}
        QSplitter::handle:vertical {{
            height: 4px;
            background: {PAGE_BG};
        }}
        QScrollArea {{
            border: none;
            background: transparent;
        }}
        """
    )
