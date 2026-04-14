"""QApplication 起動と設定検証。"""

from __future__ import annotations

import logging
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from inspection_records_search.config import (
    get_window_icon_png_path,
    validate_database_settings,
)
from inspection_records_search.services.inspection_service import (
    create_inspection_service,
)
from inspection_records_search.ui.main_window import MainWindow
from inspection_records_search.ui.theme import apply_app_theme


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    app = QApplication(sys.argv)
    icon_path = get_window_icon_png_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))
    apply_app_theme(app)

    ok, msg = validate_database_settings()
    if not ok:
        QMessageBox.critical(None, "設定エラー", msg)
        return 1

    service = create_inspection_service()
    win = MainWindow(service)
    win.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
