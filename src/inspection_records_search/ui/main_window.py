"""メインウィンドウ：サイドナビ（3画面）＋メインカード。"""

from __future__ import annotations

import datetime as dt
import traceback

from PySide6.QtCore import QEvent, Qt, QDate, QTimer
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from inspection_records_search.services.export_service import export_to_xlsx
from inspection_records_search.services.inspection_service import (
    DEFAULT_KOUTEI_FALLBACK,
    InspectionService,
)
from inspection_records_search.ui.calendar_date_input import DateFieldWidget
from inspection_records_search.ui.inspector_combo import InspectorComboBox
from inspection_records_search.ui.koutei_combo import KouteiComboBox
from inspection_records_search.ui.excel_icon import apply_excel_button_icon
from inspection_records_search.ui.processing_dialog import ProcessingDialog
from inspection_records_search.ui.table_model import RowTableModel, column_index
from inspection_records_search.ui.theme import (
    PRIMARY,
    TEXT_MAIN,
    TEXT_MUTED,
    apply_standard_table_view,
)


def _qdate_to_date(qd: QDate) -> dt.date:
    return dt.date(qd.year(), qd.month(), qd.day())


def _form_label(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setObjectName("formLabel")
    return lab


def _koutei_no_legend_html() -> str:
    """個人別画面用：工程No 凡例を1行・番号強調・読みやすい区切り（QLabel RichText）。"""
    p, m, u = PRIMARY, TEXT_MAIN, TEXT_MUTED
    # 例: 15：バリ取り,　16：ゲージ検査（カンマ＋全角スペースで項目間を空ける）
    sep = (
        f'<span style="color:{u};font-size:12px;margin:0 6px 0 14px;">,　</span>'
    )

    def pair(num: str, name: str) -> str:
        nm = name if name else ""
        return (
            f'<span style="color:{p};font-weight:700;font-size:12px;">{num}</span>'
            f'<span style="color:{u};">：</span>'
            f'<span style="color:{m};font-weight:500;">{nm}</span>'
        )

    title = (
        f'<span style="color:{p};font-weight:700;font-size:11px;'
        f"background-color:rgba(0,75,177,0.09);padding:3px 10px;"
        f'border-radius:6px;margin-right:10px;">【工程No】</span>'
    )
    pairs = [
        pair("15", "バリ取り"),
        pair("16", "ゲージ検査"),
        pair("17", "エアー吹き"),
        pair("18", "切粉除去"),
        pair("19", ""),
        pair("20", "マイクロ検"),
        pair("21", "仕掛再検査"),
        pair("22", "ボッチ取り"),
        pair("23", "在庫再検査"),
        pair("24", ""),
    ]
    # 改行なし1行（幅不足時は凡例用スクロールで閲覧）
    body = title + sep.join(pairs)
    return f'<span style="white-space:nowrap;">{body}</span>'


def _screen_header(title: str, subtitle: str) -> QWidget:
    """画面上部の大見出し＋〈補足〉。"""
    w = QWidget()
    row = QHBoxLayout(w)
    row.setContentsMargins(0, 0, 0, 20)
    row.setSpacing(0)
    t = QLabel(title)
    t.setObjectName("screenTitle")
    s = QLabel(f"〈{subtitle}〉")
    s.setObjectName("screenSubtitle")
    row.addWidget(t, alignment=Qt.AlignmentFlag.AlignBottom)
    row.addWidget(s, alignment=Qt.AlignmentFlag.AlignBottom)
    row.addStretch()
    return w


def _section_label(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setObjectName("sectionLabel")
    return lab


def _confirm_excel_export(parent: QWidget) -> bool:
    r = QMessageBox.question(
        parent,
        "確認",
        "Excel データへのエクスポートを行います。実行しますか？",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    return r == QMessageBox.StandardButton.Yes


def _show_db_error(parent: QWidget, e: BaseException) -> None:
    traceback.print_exc()
    QMessageBox.critical(parent, "データベースエラー", str(e))


# theme の QLabel#sidebarAppTitle 左右 padding（12px + 6px）と一致させること
_SIDEBAR_TITLE_PAD_H = 18


def _fit_sidebar_title_font(label: QLabel, sidebar_width_px: int) -> None:
    """サイドバー幅に収まる最大のポイントサイズにする。"""
    text = label.text()
    avail = max(int(sidebar_width_px) - _SIDEBAR_TITLE_PAD_H, 50)
    f = QFont(label.font())
    f.setWeight(QFont.Weight.ExtraBold)
    for pt in range(30, 10, -1):
        f.setPointSize(pt)
        if QFontMetrics(f).horizontalAdvance(text) <= avail:
            label.setFont(f)
            return
    f.setPointSize(10)
    label.setFont(f)


# 検索・照会条件の入力行と、その下のボタン行の間の余白（全ページで統一）
_FILTER_TO_ACTIONS_TOP_SPACING = 10


class InspectorAggregatePage(QWidget):
    """検査員別集計（メイン明細・VBA 上段サブフォーム相当）。"""

    def __init__(self, service: InspectionService, parent=None) -> None:
        super().__init__(parent)
        self._svc = service

        self._date_kaishibi = DateFieldWidget()
        self._date_shuryobi = DateFieldWidget()

        self._hinban = QLineEdit()
        self._hinban.setPlaceholderText("品番（任意）")

        btn_run = QPushButton("表示")
        btn_run.setObjectName("primaryButton")
        btn_run.clicked.connect(self._on_show_detail)

        self._table = QTableView()
        self._model = RowTableModel([], [])
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        apply_standard_table_view(self._table)

        btn_x = QPushButton("Excel 出力（外観検査集計）")
        btn_x.setObjectName("outlineButton")
        apply_excel_button_icon(btn_x)
        btn_x.clicked.connect(self._on_export)

        filter_box = QGroupBox("検索条件")
        fl = QVBoxLayout(filter_box)
        # 表示開始日・表示終了日・品番を一行
        self._date_kaishibi.setMaximumWidth(200)
        self._date_shuryobi.setMaximumWidth(200)
        row_filter = QHBoxLayout()
        row_filter.setSpacing(4)
        row_filter.addWidget(_form_label("表示開始日"))
        row_filter.addWidget(self._date_kaishibi, 0)
        row_filter.addSpacing(12)
        row_filter.addWidget(_form_label("表示終了日"))
        row_filter.addWidget(self._date_shuryobi, 0)
        row_filter.addSpacing(12)
        row_filter.addWidget(_form_label("品番"))
        row_filter.addWidget(self._hinban, stretch=1)
        fl.addLayout(row_filter)
        fl.addSpacing(_FILTER_TO_ACTIONS_TOP_SPACING)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addWidget(btn_run)
        btn_row.addWidget(btn_x)
        btn_row.addStretch()
        fl.addLayout(btn_row)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(
            _screen_header("検査員別集計", "表示開始日〜表示終了日・品番で明細を検索")
        )
        root.addWidget(filter_box)
        root.addWidget(_section_label("検査員別明細"))
        root.addWidget(self._table, stretch=1)

    def _on_show_detail(self) -> None:
        d0 = _qdate_to_date(self._date_kaishibi.date())
        d1 = _qdate_to_date(self._date_shuryobi.date())
        if d0 > d1:
            QMessageBox.warning(
                self,
                "日付の確認",
                "表示開始日が表示終了日より後になっています。日付を修正してください。",
            )
            return
        hinban = self._hinban.text() or None

        def task():
            return self._svc.fetch_main_detail(d0, d1, hinban)

        def on_success(res: object) -> None:
            headers, rows = res  # type: ignore[misc]
            self._model.set_data(headers, rows)
            for name in ("ID", "集計除外フラグ"):
                idx = column_index(headers, name)
                if idx is not None:
                    self._table.setColumnHidden(idx, True)

        ProcessingDialog.run_task(
            self,
            title="検査員別集計",
            subtitle="データを検索しています。",
            task=task,
            on_success=on_success,
            on_error=lambda e: _show_db_error(self, e),
        )

    def _on_export(self) -> None:
        if not _confirm_excel_export(self):
            return
        if not self._model.raw_rows():
            QMessageBox.warning(
                self, "出力不可", "出力出来るデータがありません。"
            )
            return
        db_path = self._svc.db_path
        headers = self._model.headers()
        rows = self._model.raw_rows()

        def task():
            return export_to_xlsx(
                db_path, "外観検査集計.xlsx", headers, rows
            )

        def on_success(path: object) -> None:
            QMessageBox.information(
                self, "確認", f"Excel ファイルへ保存しました。\n{path}"
            )

        ProcessingDialog.run_task(
            self,
            title="Excel 出力",
            subtitle="ファイルを作成しています。",
            task=task,
            on_success=on_success,
            on_error=lambda e: _show_db_error(self, e),
        )


class LotAggregatePage(QWidget):
    """生産ロットID別集計（Q_生産ロット集計）。"""

    def __init__(self, service: InspectionService, parent=None) -> None:
        super().__init__(parent)
        self._svc = service

        self._hinban = QLineEdit()
        self._hinban.setPlaceholderText("品番（任意）")
        self._hinban.setMaximumWidth(260)
        self._koutei = KouteiComboBox()
        self._koutei.setMaximumWidth(220)
        self._load_koutei_items()

        btn_lot = QPushButton("表示")
        btn_lot.setObjectName("primaryButton")
        btn_lot.clicked.connect(self._on_show_lot)

        self._table = QTableView()
        self._model = RowTableModel([], [])
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        apply_standard_table_view(self._table)
        # 列数が少ないため最終列を伸ばさない（数量と作業時間の合計の間に空白が広がらない）
        self._table.horizontalHeader().setStretchLastSection(False)

        btn_x = QPushButton("Excel 出力（ロット別集計）")
        btn_x.setObjectName("outlineButton")
        apply_excel_button_icon(btn_x)
        btn_x.clicked.connect(self._on_export)

        lot_box = QGroupBox("検索条件")
        ll = QVBoxLayout(lot_box)
        lr = QHBoxLayout()
        lr.setSpacing(4)
        lr.addWidget(_form_label("品番"))
        lr.addWidget(self._hinban, 0)
        lr.addSpacing(12)
        lr.addWidget(_form_label("工程No"))
        lr.addWidget(self._koutei, 0)
        lr.addStretch()
        ll.addLayout(lr)
        ll.addSpacing(_FILTER_TO_ACTIONS_TOP_SPACING)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addWidget(btn_lot)
        btn_row.addWidget(btn_x)
        btn_row.addStretch()
        ll.addLayout(btn_row)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(
            _screen_header("生産ロットID別集計", "ロット単位の集計表示")
        )
        root.addWidget(lot_box)
        root.addWidget(_section_label("ロット別集計結果"))
        root.addWidget(self._table, stretch=1)

    def _load_koutei_items(self) -> None:
        """工程No 候補：DB に値があればそれを、無ければ既定10件。"""
        try:
            opts = self._svc.fetch_koutei_distinct_values()
        except Exception:  # noqa: BLE001
            opts = []
        if not opts:
            opts = list(DEFAULT_KOUTEI_FALLBACK)
        self._koutei.clear()
        for s in opts:
            self._koutei.addItem(s, s)
        self._koutei.setCurrentIndex(-1)
        le = self._koutei.lineEdit()
        if le is not None:
            le.clear()

    def _on_show_lot(self) -> None:
        hb = self._hinban.text() or None
        kt = self._koutei.resolved_koutei_filter()

        def task():
            return self._svc.fetch_lot_aggregate(hb, kt)

        def on_success(res: object) -> None:
            headers, rows = res  # type: ignore[misc]
            self._model.set_data(headers, rows)

        ProcessingDialog.run_task(
            self,
            title="生産ロットID別集計",
            subtitle="集計しています。",
            task=task,
            on_success=on_success,
            on_error=lambda e: _show_db_error(self, e),
        )

    def _on_export(self) -> None:
        if not _confirm_excel_export(self):
            return
        if not self._model.raw_rows():
            QMessageBox.warning(
                self, "出力不可", "出力出来るデータがありません。"
            )
            return
        db_path = self._svc.db_path
        headers = self._model.headers()
        rows = self._model.raw_rows()

        def task():
            return export_to_xlsx(
                db_path, "外観検査ロット別集計.xlsx", headers, rows
            )

        def on_success(path: object) -> None:
            QMessageBox.information(
                self, "確認", f"Excel ファイルへ保存しました。\n{path}"
            )

        ProcessingDialog.run_task(
            self,
            title="Excel 出力",
            subtitle="ファイルを作成しています。",
            task=task,
            on_success=on_success,
            on_error=lambda e: _show_db_error(self, e),
        )


class PersonalInquiryPage(QWidget):
    """個人別データ照会（VBA f_個人別照会 相当）。"""

    def __init__(self, service: InspectionService, parent=None) -> None:
        super().__init__(parent)
        self._svc = service

        self._cbo = InspectorComboBox()
        self._cbo.setMinimumWidth(220)
        self._cbo.setMaximumWidth(400)

        self._date_kaishibi = DateFieldWidget()
        self._date_shuryobi = DateFieldWidget()

        btn = QPushButton("表示")
        btn.setObjectName("primaryButton")
        btn.clicked.connect(self._on_show)

        self._t1 = QTableView()
        self._m1 = RowTableModel([], [])
        self._t1.setModel(self._m1)
        self._t1.setAlternatingRowColors(True)
        self._t1.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        apply_standard_table_view(self._t1)

        self._t2 = QTableView()
        self._m2 = RowTableModel([], [])
        self._t2.setModel(self._m2)
        self._t2.setAlternatingRowColors(True)
        self._t2.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        apply_standard_table_view(self._t2)
        # 数量と作業時間の間に余白が広がらないよう最終列を伸ばさない
        self._t2.horizontalHeader().setStretchLastSection(False)

        top = QGroupBox("照会条件")
        tl = QVBoxLayout(top)
        # 検査員・表示開始日・表示終了日を一行（日付は固定幅）
        self._date_kaishibi.setMaximumWidth(200)
        self._date_shuryobi.setMaximumWidth(200)
        row = QHBoxLayout()
        row.setSpacing(4)
        row.addWidget(_form_label("検査員"))
        row.addWidget(self._cbo, 0)
        row.addSpacing(12)
        row.addWidget(_form_label("表示開始日"))
        row.addWidget(self._date_kaishibi, 0)
        row.addSpacing(12)
        row.addWidget(_form_label("表示終了日"))
        row.addWidget(self._date_shuryobi, 0)
        row.addStretch(1)
        tl.addLayout(row)
        tl.addSpacing(_FILTER_TO_ACTIONS_TOP_SPACING)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addWidget(btn, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        # 凡例を表示ボタン付近に置く（間に伸びるストレッチは入れない）
        btn_row.addSpacing(8)
        legend_lbl = QLabel(_koutei_no_legend_html())
        legend_lbl.setObjectName("kouteiLegend")
        legend_lbl.setTextFormat(Qt.TextFormat.RichText)
        legend_lbl.setWordWrap(False)
        legend_lbl.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        legend_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.NoTextInteraction
        )
        legend_lbl.adjustSize()
        legend_lbl.setMinimumHeight(legend_lbl.sizeHint().height())
        legend_scroll = QScrollArea()
        legend_scroll.setObjectName("kouteiLegendScroll")
        legend_scroll.setWidget(legend_lbl)
        legend_scroll.setWidgetResizable(False)
        legend_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        legend_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        legend_scroll.setFrameShape(QFrame.Shape.NoFrame)
        legend_scroll.setFixedHeight(max(30, legend_lbl.sizeHint().height() + 8))
        legend_scroll.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        btn_row.addWidget(legend_scroll, stretch=1)
        tl.addLayout(btn_row)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self._wrap("外観検査記録（明細）", self._t1))
        split.addWidget(self._wrap("外観検査集計", self._t2))
        split.setChildrenCollapsible(False)
        split.setStretchFactor(0, 1)
        split.setStretchFactor(1, 1)
        split.setSizes([560, 560])

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(
            _screen_header(
                "個人別データ照会",
                "検査員・表示開始日〜表示終了日で記録と集計",
            )
        )
        lay.addWidget(top)
        lay.addWidget(split, stretch=1)

        self._load_inspectors()

    def _wrap(self, title: str, view: QTableView) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 8, 0, 0)
        v.addWidget(_section_label(title))
        v.addWidget(view, stretch=1)
        return w

    def _load_inspectors(self) -> None:
        """起動時はモーダルなしで同期読込（スピナーは出さない）。"""
        try:
            headers, rows = self._svc.fetch_inspectors()
            self._cbo.clear()
            if "検査員ID" in headers and "検査員名" in headers:
                i_id = headers.index("検査員ID")
                i_nm = headers.index("検査員名")
            else:
                i_id, i_nm = 0, 1
            for r in rows:
                qid = r[i_id]
                name = r[i_nm]
                label = f"{qid}  {name}"
                self._cbo.addItem(label, str(qid))
            if self._cbo.count() > 0:
                self._cbo.setCurrentIndex(0)
        except Exception as e:  # noqa: BLE001
            QMessageBox.warning(
                self,
                "検査員一覧",
                f"検査員マスタの取得に失敗しました。\n{e}",
            )

    def _on_show(self) -> None:
        kid = self._cbo.resolved_kensain_id()
        if not kid:
            QMessageBox.critical(
                self,
                "確認",
                "検査員を一覧から選ぶか、表示に一致するID・氏名を入力してください。",
            )
            return

        d0 = _qdate_to_date(self._date_kaishibi.date())
        d1 = _qdate_to_date(self._date_shuryobi.date())
        if d0 > d1:
            QMessageBox.warning(
                self,
                "日付の確認",
                "表示開始日が表示終了日より後になっています。日付を修正してください。",
            )
            return
        kid_s = str(kid)

        def task():
            h1, r1 = self._svc.fetch_personal_records(kid_s, d0, d1)
            h2, r2 = self._svc.fetch_personal_summary(kid_s, d0, d1)
            return h1, r1, h2, r2

        def on_success(res: object) -> None:
            h1, r1, h2, r2 = res  # type: ignore[misc]
            self._m1.set_data(h1, r1)
            idx = column_index(h1, "検査員ID")
            if idx is not None:
                self._t1.setColumnHidden(idx, True)
            self._m2.set_data(h2, r2)
            idx2 = column_index(h2, "検査員ID")
            if idx2 is not None:
                self._t2.setColumnHidden(idx2, True)

        ProcessingDialog.run_task(
            self,
            title="個人別データ照会",
            subtitle="データを検索しています。",
            task=task,
            on_success=on_success,
            on_error=lambda e: _show_db_error(self, e),
        )


class MainWindow(QWidget):
    """サイドバー＋メインカード＋3ページ。"""

    def __init__(self, db_path: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("appRoot")
        self.setWindowTitle("外観検査記録照会")
        # 最大化解除時の初期サイズ（スナップ分割時は OS がリサイズ）
        self.resize(1220, 800)
        self.setMinimumSize(800, 560)

        self._svc = InspectionService(db_path)

        self._sidebar = QFrame()
        self._sidebar.setObjectName("sidebar")
        sv = QVBoxLayout(self._sidebar)
        sv.setContentsMargins(0, 24, 0, 24)
        sv.setSpacing(0)

        self._sidebar_title = QLabel("外観検査記録照会")
        self._sidebar_title.setObjectName("sidebarAppTitle")
        sv.addWidget(self._sidebar_title)
        subtitle = QLabel("照会・集計・Excel 出力")
        subtitle.setObjectName("sidebarTagline")
        sv.addWidget(subtitle)
        sv.addSpacing(20)

        btn_inspector = QPushButton("検査員別集計")
        btn_lot = QPushButton("生産ロットID別集計")
        btn_personal = QPushButton("個人別データ照会")
        nav_buttons = (btn_inspector, btn_lot, btn_personal)
        for b in nav_buttons:
            b.setObjectName("sidebarNav")
            b.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
            )
            b.setCheckable(True)
        sv.addWidget(btn_inspector)
        sv.addWidget(btn_lot)
        sv.addWidget(btn_personal)
        sv.addStretch()

        self._sidebar.installEventFilter(self)
        QTimer.singleShot(0, self._refit_sidebar_title)

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        for i, btn in enumerate(nav_buttons):
            self._nav_group.addButton(btn, i)
        self._nav_group.idClicked.connect(self._on_nav)

        self._stack = QStackedWidget()
        self._page_inspector = InspectorAggregatePage(self._svc)
        self._page_lot = LotAggregatePage(self._svc)
        self._page_personal = PersonalInquiryPage(self._svc)
        self._stack.addWidget(self._page_inspector)
        self._stack.addWidget(self._page_lot)
        self._stack.addWidget(self._page_personal)

        btn_inspector.setChecked(True)

        content_shell = QWidget()
        content_shell.setObjectName("contentShell")
        shell_lay = QVBoxLayout(content_shell)
        shell_lay.setContentsMargins(20, 20, 24, 24)

        card = QFrame()
        card.setObjectName("contentCard")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(28, 28, 28, 28)
        card_lay.addWidget(self._stack)
        shell_lay.addWidget(card, stretch=1)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._sidebar)
        body.addWidget(content_shell, stretch=1)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addLayout(body)

    def _refit_sidebar_title(self) -> None:
        if self._sidebar.width() > 0:
            _fit_sidebar_title_font(self._sidebar_title, self._sidebar.width())

    def eventFilter(self, obj, event):  # noqa: ANN001
        if obj is self._sidebar and event.type() == QEvent.Type.Resize:
            self._refit_sidebar_title()
        return super().eventFilter(obj, event)

    def resizeEvent(self, event) -> None:  # noqa: ANN001, N802
        # スナップ分割・最大化の切り替え後もタイトル・レイアウトに追従
        super().resizeEvent(event)
        self._refit_sidebar_title()

    def _on_nav(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
