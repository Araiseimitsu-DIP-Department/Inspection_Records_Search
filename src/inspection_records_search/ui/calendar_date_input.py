"""クリックで開くカスタムカレンダーと日付表示フィールド。"""

from __future__ import annotations

import calendar as pycal
from datetime import date

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QDate, Signal
from PySide6.QtGui import QColor, QGuiApplication, QShowEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from inspection_records_search.ui.theme import INPUT_BG, PRIMARY, TEXT_MAIN


def _position_calendar_near_anchor(dlg: QDialog, anchor: QWidget) -> None:
    """クリックされた入力付近に表示。下にはみ出す場合は上側へ。画面外には出さない。"""
    margin = 6
    dlg.adjustSize()
    w = dlg.width()
    h = dlg.height()
    below_left = anchor.mapToGlobal(QPoint(0, anchor.height() + margin))
    screen = QGuiApplication.screenAt(below_left) or QGuiApplication.primaryScreen()
    ag = screen.availableGeometry()

    x, y = below_left.x(), below_left.y()
    if y + h > ag.bottom():
        y = anchor.mapToGlobal(QPoint(0, -margin)).y() - h
    if x + w > ag.right():
        x = max(ag.left(), ag.right() - w)
    if x < ag.left():
        x = ag.left()
    if y < ag.top():
        y = ag.top()
    if y + h > ag.bottom():
        y = max(ag.top(), ag.bottom() - h)
    dlg.move(x, y)


class StyledCalendarDialog(QDialog):
    """添付イメージに近い月表示カレンダー（日曜始まり）。"""

    def __init__(
        self,
        initial: QDate,
        parent: QWidget | None = None,
        anchor: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._anchor = anchor
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._selected = QDate(initial)
        self._view = QDate(initial.year(), initial.month(), 1)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 28, 28, 28)

        card = QFrame()
        card.setObjectName("calendarCard")
        card.setStyleSheet(
            f"""
            QFrame#calendarCard {{
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E2E8F0;
            }}
            """
        )
        sh = QGraphicsDropShadowEffect(card)
        sh.setBlurRadius(28)
        sh.setOffset(0, 8)
        sh.setColor(QColor(0, 0, 0, 55))
        card.setGraphicsEffect(sh)

        root = QVBoxLayout(card)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(12)

        # 1 行目: Prev / 年月 / Next
        row_nav = QHBoxLayout()
        self._btn_prev = QPushButton("Prev")
        self._btn_next = QPushButton("Next")
        for b in (self._btn_prev, self._btn_next):
            b.setStyleSheet(self._nav_btn_style())
            b.setMinimumWidth(72)
        self._title = QLabel()
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet(
            "font-size: 17px; font-weight: 800; color: #1a1f26;"
        )
        row_nav.addWidget(self._btn_prev)
        row_nav.addStretch()
        row_nav.addWidget(self._title)
        row_nav.addStretch()
        row_nav.addWidget(self._btn_next)
        root.addLayout(row_nav)

        # 2 行目: 今日 / 閉じる
        row_top = QHBoxLayout()
        self._btn_today = QPushButton("今日")
        self._btn_close = QPushButton("閉じる")
        for b in (self._btn_today, self._btn_close):
            b.setStyleSheet(self._nav_btn_style())
        row_top.addWidget(self._btn_today)
        row_top.addStretch()
        row_top.addWidget(self._btn_close)
        root.addLayout(row_top)

        self._grid = QGridLayout()
        self._grid.setHorizontalSpacing(4)
        self._grid.setVerticalSpacing(4)
        root.addLayout(self._grid)

        row_btns = QHBoxLayout()
        row_btns.addStretch()
        btn_cancel = QPushButton("キャンセル")
        btn_cancel.setStyleSheet(self._secondary_btn_style())
        btn_ok = QPushButton("この日を選択")
        btn_ok.setStyleSheet(self._primary_btn_style())
        btn_ok.setMinimumWidth(140)
        row_btns.addWidget(btn_cancel)
        row_btns.addWidget(btn_ok)
        root.addLayout(row_btns)

        outer.addWidget(card)

        self._btn_prev.clicked.connect(self._prev_month)
        self._btn_next.clicked.connect(self._next_month)
        self._btn_today.clicked.connect(self._go_today)
        self._btn_close.clicked.connect(self.reject)
        btn_cancel.clicked.connect(self.reject)
        btn_ok.clicked.connect(self.accept)

        self._rebuild_grid()
        self.setFixedSize(360, 460)

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        if self._anchor is not None:
            _position_calendar_near_anchor(self, self._anchor)

    def selected_date(self) -> QDate:
        return self._selected

    @staticmethod
    def _nav_btn_style() -> str:
        return """
            QPushButton {
                background-color: #ECEFF3;
                color: #1a1f26;
                border: none;
                border-radius: 8px;
                padding: 8px 12px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #dde3ea; }
        """

    @staticmethod
    def _secondary_btn_style() -> str:
        return """
            QPushButton {
                background-color: #ECEFF3;
                color: #1a1f26;
                border: none;
                border-radius: 9px;
                padding: 10px 18px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #dde3ea; }
        """

    @staticmethod
    def _primary_btn_style() -> str:
        return f"""
            QPushButton {{
                background-color: {PRIMARY};
                color: #FFFFFF;
                border: none;
                border-radius: 9px;
                padding: 10px 18px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: #003A8C; }}
        """

    def _prev_month(self) -> None:
        self._view = self._view.addMonths(-1)
        self._rebuild_grid()

    def _next_month(self) -> None:
        self._view = self._view.addMonths(1)
        self._rebuild_grid()

    def _go_today(self) -> None:
        t = QDate.currentDate()
        self._selected = t
        self._view = QDate(t.year(), t.month(), 1)
        self._rebuild_grid()

    def _rebuild_grid(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        y, m = self._view.year(), self._view.month()
        self._title.setText(f"{y}.{m:02d}")

        headers = ("日", "月", "火", "水", "木", "金", "土")
        for c, t in enumerate(headers):
            lab = QLabel(t)
            lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if c in (0, 6):
                lab.setStyleSheet(
                    "color: #c62828; font-weight: 700; font-size: 12px;"
                )
            else:
                lab.setStyleSheet(
                    "color: #1a1f26; font-weight: 600; font-size: 12px;"
                )
            self._grid.addWidget(lab, 0, c)

        cal = pycal.Calendar(firstweekday=pycal.SUNDAY)
        weeks = cal.monthdatescalendar(y, m)
        for r, week in enumerate(weeks):
            for c, d in enumerate(week):
                qd = QDate(d.year, d.month, d.day)
                btn = QPushButton(str(d.day))
                btn.setFixedSize(42, 36)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                self._style_day_button(btn, d, y, m, qd)
                btn.clicked.connect(
                    lambda *_, dd=d: self._on_day_clicked(dd)
                )
                self._grid.addWidget(btn, r + 1, c)

    def _style_day_button(
        self,
        btn: QPushButton,
        d: date,
        view_y: int,
        view_m: int,
        qd: QDate,
    ) -> None:
        in_month = d.month == view_m and d.year == view_y
        dow = qd.dayOfWeek()  # Qt: 月=1 … 日=7
        weekend = dow in (6, 7)

        if qd == self._selected:
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {PRIMARY};
                    color: #FFFFFF;
                    border: none;
                    border-radius: 8px;
                    font-weight: 800;
                    font-size: 13px;
                }}
                """
            )
            return

        if not in_month:
            btn.setStyleSheet(
                """
                QPushButton {
                    background: transparent;
                    color: #b8c0c8;
                    border: none;
                    font-weight: 500;
                    font-size: 13px;
                }
                """
            )
            return

        fg = "#c62828" if weekend else "#1a1f26"
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                color: {fg};
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: rgba(0, 75, 177, 0.08);
            }}
            """
        )

    def _on_day_clicked(self, d: date) -> None:
        self._selected = QDate(d.year, d.month, d.day)
        if d.month != self._view.month() or d.year != self._view.year():
            self._view = QDate(d.year, d.month, 1)
        self._rebuild_grid()


class DateFieldWidget(QFrame):
    """矢印なし。クリックで StyledCalendarDialog を開く。"""

    dateChanged = Signal(QDate)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._date = QDate.currentDate()
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self._line = QLineEdit()
        self._line.setObjectName("dateFieldDisplay")
        self._line.setReadOnly(True)
        self._line.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._line.setCursor(Qt.CursorShape.PointingHandCursor)
        self._line.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._line.setStyleSheet(
            f"""
            QLineEdit#dateFieldDisplay {{
                background-color: {INPUT_BG};
                border: none;
                border-radius: 9px;
                padding: 8px 12px;
                min-height: 22px;
                color: {TEXT_MAIN};
                font-size: 13px;
            }}
            """
        )
        lay.addWidget(self._line)
        self._sync_display()
        self._line.installEventFilter(self)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802
        if obj is self._line and event.type() == QEvent.Type.MouseButtonPress:
            self._open_calendar()
            return True
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event) -> None:  # noqa: ANN001
        self._open_calendar()
        super().mousePressEvent(event)

    def _sync_display(self) -> None:
        self._line.setText(self._date.toString("yyyy/MM/dd"))

    def date(self) -> QDate:
        return self._date

    def setDate(self, d: QDate) -> None:
        self._date = d
        self._sync_display()
        self.dateChanged.emit(d)

    def _open_calendar(self) -> None:
        host = self.window()
        dlg = StyledCalendarDialog(self._date, parent=host, anchor=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.setDate(dlg.selected_date())
