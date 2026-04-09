"""検査員選択：編集＋候補絞り込み、ポップアップ高さの調整。"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QEvent, QPoint, QTimer, Qt
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtWidgets import QComboBox, QCompleter


class InspectorComboBox(QComboBox):
    """編集可能・QCompleter で部分一致絞り込み。リスト開いたときは行数に合わせて高さ調整。"""

    _MAX_VISIBLE_ROWS = 8

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("inspectorCombo")
        self.setMaxVisibleItems(self._MAX_VISIBLE_ROWS)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        le = self.lineEdit()
        if le is not None:
            le.setPlaceholderText("検査員ID・名前で絞り込み")
            # 入力のたびに候補ポップの位置を再計算（Qt 既定位置で入力と重なるのを防ぐ）
            le.textChanged.connect(
                lambda _t: QTimer.singleShot(0, self._reposition_completer_popup)
            )
            # 入力欄のどこをクリックしても全件リストを開く（右端24pxも従来どおり）
            le.installEventFilter(self)

        v = self.view()
        v.setUniformItemSizes(True)
        v.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        v.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        v.setMinimumHeight(0)

        comp = QCompleter(self.model(), self)
        comp.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        comp.setFilterMode(Qt.MatchFlag.MatchContains)
        comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp.setMaxVisibleItems(self._MAX_VISIBLE_ROWS)
        self.setCompleter(comp)
        comp.activated[str].connect(self._on_completion_chosen)

        self._completer_popup = comp.popup()
        self._completer_popup.setObjectName("inspectorCompleterPopup")
        self._completer_popup.setUniformItemSizes(True)
        self._completer_popup.setMaximumHeight(280)
        self._completer_popup.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._completer_popup.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        # 表示直後に Qt 既定位置を上書き（入力欄と重ならないよう直下へ）
        self._completer_popup.installEventFilter(self)

    def _reposition_completer_popup(self) -> None:
        """絞り込み候補リストをラインエディットの直下に配置（画面端では上に逃がす）。"""
        comp = self.completer()
        if comp is None:
            return
        pop = comp.popup()
        le = self.lineEdit()
        if pop is None or le is None or not pop.isVisible():
            return
        margin = 4
        pop.adjustSize()
        w = max(pop.sizeHint().width(), self.width())
        h = pop.height()
        pop.resize(w, h)

        x = le.mapToGlobal(QPoint(0, 0)).x()
        y = le.mapToGlobal(QPoint(0, le.height() + margin)).y()

        pt = QPoint(x, y)
        screen = QGuiApplication.screenAt(pt) or QGuiApplication.primaryScreen()
        ag = screen.availableGeometry()

        if y + h > ag.bottom() - 8:
            y = le.mapToGlobal(QPoint(0, -margin)).y() - h
        y = max(ag.top(), min(y, ag.bottom() - h))
        if x + w > ag.right() - 4:
            x = max(ag.left(), ag.right() - w - 4)
        x = max(ag.left(), x)

        pop.setGeometry(x, y, w, h)

    def eventFilter(self, obj, event) -> bool:  # noqa: ANN001, N802
        if (
            getattr(self, "_completer_popup", None) is not None
            and obj is self._completer_popup
            and event.type() == QEvent.Type.Show
        ):
            # Qt 内部の配置の後に上書き（1ms でもう一度当てると環境差に強い）
            QTimer.singleShot(0, self._reposition_completer_popup)
            QTimer.singleShot(1, self._reposition_completer_popup)

        le = self.lineEdit()
        if (
            le is not None
            and obj is le
            and event.type() == QEvent.Type.MouseButtonPress
            and isinstance(event, QMouseEvent)
            and event.button() == Qt.MouseButton.LeftButton
        ):
            # フォーカス処理の後に全件ポップアップを開く
            QTimer.singleShot(0, self.showPopup)
        return super().eventFilter(obj, event)

    def _on_completion_chosen(self, text: str) -> None:
        idx = self.findText(text, Qt.MatchFlag.MatchExactly)
        if idx >= 0:
            self.setCurrentIndex(idx)

    def resolved_kensain_id(self) -> Optional[str]:
        """表示用テキストから検査員IDを解決（表示・完全一致・一意の部分一致）。"""
        text = self.currentText().strip()
        if not text:
            return None
        idx = self.currentIndex()
        if idx >= 0 and self.itemText(idx).strip() == text:
            d = self.itemData(idx)
            return str(d) if d is not None else None
        j = self.findText(text, Qt.MatchFlag.MatchExactly)
        if j >= 0:
            d = self.itemData(j)
            return str(d) if d is not None else None
        tcf = text.casefold()
        for i in range(self.count()):
            if self.itemText(i).strip().casefold() == tcf:
                d = self.itemData(i)
                return str(d) if d is not None else None
        candidates = [
            i
            for i in range(self.count())
            if tcf in self.itemText(i).casefold()
        ]
        if len(candidates) == 1:
            i = candidates[0]
            self.setCurrentIndex(i)
            self.setCurrentText(self.itemText(i))
            d = self.itemData(i)
            return str(d) if d is not None else None
        return None

    def showPopup(self) -> None:
        super().showPopup()
        QTimer.singleShot(0, self._fit_popup_to_rows)

    def hidePopup(self) -> None:
        v = self.view()
        if v is not None:
            v.setMaximumHeight(16777215)
            v.setMinimumHeight(0)
        super().hidePopup()

    def _fit_popup_to_rows(self) -> None:
        v = self.view()
        if v is None or self.count() == 0:
            return
        visible = min(self.count(), self._MAX_VISIBLE_ROWS)
        rh = v.sizeHintForRow(0)
        if rh < 1:
            rh = max(34, v.fontMetrics().height() + 18)
        pad_v = 20
        list_h = visible * rh + pad_v
        v.setMinimumHeight(0)
        v.setMaximumHeight(list_h)

        popup = v.window()
        if popup is None or popup is self or not popup.isWindow():
            return
        frame_extra = 10
        target_h = list_h + frame_extra
        popup.resize(max(popup.width(), self.width()), target_h)
