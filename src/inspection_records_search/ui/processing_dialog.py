"""処理中モーダル（PROCESS バッジ・スピナー）とバックグラウンド実行。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from PySide6.QtCore import QObject, QThread, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

T = TypeVar("T")

PRIMARY_SPIN = "#004aad"
RING_BG = "#D8DEE6"


class SpinnerWidget(QWidget):
    """円弧が回転するローディング表示。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.setFixedSize(56, 56)

    def _tick(self) -> None:
        # Qt drawArc の start 進行を時計回りに見せる（毎フレーム減算）
        self._angle = (self._angle - 10 + 360) % 360
        self.update()

    def showEvent(self, event) -> None:  # noqa: ANN001
        self._timer.start(45)
        super().showEvent(event)

    def hideEvent(self, event) -> None:  # noqa: ANN001
        self._timer.stop()
        super().hideEvent(event)

    def paintEvent(self, event) -> None:  # noqa: ANN001
        del event
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        m = 4
        d = min(self.width(), self.height()) - 2 * m
        x = (self.width() - d) // 2
        y = (self.height() - d) // 2

        pen_bg = QPen(QColor(RING_BG))
        pen_bg.setWidth(4)
        p.setPen(pen_bg)
        p.drawEllipse(x, y, d, d)

        pen_fg = QPen(QColor(PRIMARY_SPIN))
        pen_fg.setWidth(4)
        pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen_fg)
        # 1/16 度単位
        start = self._angle * 16
        span = 100 * 16
        p.drawArc(x, y, d, d, start, span)


class _Worker(QObject):
    """ワーカースレッド上で callable を実行する。"""

    finished = Signal(object)
    failed = Signal(object)

    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self._fn = fn

    @Slot()
    def execute(self) -> None:
        try:
            self.finished.emit(self._fn())
        except BaseException as e:  # noqa: BLE001
            self.failed.emit(e)


class ProcessingDialog(QDialog):
    """参考デザインに近い処理中ダイアログ。"""

    def __init__(
        self,
        title: str,
        subtitle: str,
        parent: QWidget | None = None,
        *,
        badge_text: str = "PROCESS",
    ) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._thread: QThread | None = None
        self._worker: _Worker | None = None
        self._result: Any = None
        self._error: BaseException | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 32, 32, 32)

        card = QFrame()
        card.setObjectName("processingCard")
        card.setStyleSheet(
            """
            QFrame#processingCard {
                background-color: #FFFFFF;
                border-radius: 26px;
                border: 1px solid #E8ECF0;
            }
            """
        )
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 50))
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(14)

        top = QHBoxLayout()
        top.setSpacing(12)
        badge = QLabel(badge_text)
        badge.setStyleSheet(
            """
            QLabel {
                background-color: #D7E6FF;
                color: #004BB1;
                padding: 5px 14px;
                border-radius: 999px;
                font-weight: 800;
                font-size: 10px;
                letter-spacing: 0.08em;
            }
            """
        )
        tit = QLabel(title)
        tit.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: 800;
                color: #1a1f26;
            }
            """
        )
        top.addWidget(badge, alignment=Qt.AlignmentFlag.AlignTop)
        top.addWidget(tit, alignment=Qt.AlignmentFlag.AlignTop)
        top.addStretch()
        lay.addLayout(top)

        sub = QLabel(subtitle)
        sub.setStyleSheet("font-size: 13px; color: #5c6570;")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        lay.addSpacing(20)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(SpinnerWidget())
        row.addStretch()
        lay.addLayout(row)

        outer.addWidget(card)
        self.setFixedSize(440, 280)

    def _slot_ok(self, result: object) -> None:
        self._result = result
        self._error = None
        self._teardown_thread()
        self.accept()

    def _slot_fail(self, err: object) -> None:
        self._result = None
        self._error = err if isinstance(err, BaseException) else RuntimeError(str(err))
        self._teardown_thread()
        self.accept()

    def _teardown_thread(self) -> None:
        if self._thread is not None:
            if self._thread.isRunning():
                self._thread.quit()
                self._thread.wait(120_000)
            self._thread.deleteLater()
            self._thread = None
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None

    @classmethod
    def run_task(
        cls,
        parent: QWidget | None,
        title: str,
        subtitle: str,
        task: Callable[[], T],
        on_success: Callable[[T], None],
        on_error: Callable[[BaseException], None] | None = None,
    ) -> None:
        """
        モーダルを表示しつつ task を別スレッドで実行する。
        完了後に on_success / on_error をメインスレッドから呼ぶ。
        """
        dlg = cls(title, subtitle, parent)
        thread = QThread(dlg)
        worker = _Worker(task)
        worker.moveToThread(thread)
        dlg._thread = thread
        dlg._worker = worker

        thread.started.connect(worker.execute)
        worker.finished.connect(dlg._slot_ok)
        worker.failed.connect(dlg._slot_fail)
        thread.start()
        dlg.exec()

        err = dlg._error
        if err is not None:
            if on_error is not None:
                on_error(err)
            return
        on_success(dlg._result)
