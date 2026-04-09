"""QApplication 起動と設定検証。"""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from inspection_records_search.config import (
    get_access_db_path,
    get_window_icon_png_path,
    validate_access_db_path,
)
from inspection_records_search.ui.main_window import MainWindow
from inspection_records_search.ui.theme import apply_app_theme


def main() -> int:
    app = QApplication(sys.argv)
    icon_path = get_window_icon_png_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))
    apply_app_theme(app)

    db_path = get_access_db_path()
    ok, msg = validate_access_db_path(db_path)
    if not ok:
        QMessageBox.critical(None, "設定エラー", msg)
        return 1

    win = MainWindow(db_path)
    win.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
