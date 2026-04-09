"""工程No 選択：検査員コンボと同一スタイル・挙動（編集・候補絞り込み）。"""

from __future__ import annotations

from typing import Optional

from inspection_records_search.ui.inspector_combo import InspectorComboBox


class KouteiComboBox(InspectorComboBox):
    """ロット別集計の工程No 用。objectName は親と同じ inspectorCombo（テーマ共通）。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        le = self.lineEdit()
        if le is not None:
            le.setPlaceholderText("工程No（任意）")

    def resolved_koutei_filter(self) -> Optional[str]:
        """照会条件に渡す工程No（空なら絞り込みなし）。"""
        t = self.currentText().strip()
        return t if t else None
