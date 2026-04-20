"""Application entry point for the pywebview frontend."""

from __future__ import annotations

import logging
import os

# Force the Qt binding so the frozen executable does not depend on
# Windows WebView2 runtime.
os.environ.setdefault("QT_API", "pyqt6")

import webview

from inspection_records_search.config import get_window_icon_png_path, validate_database_settings
from inspection_records_search.services.inspection_service import create_inspection_service
from inspection_records_search.webview_app import AppBootstrap, WebAppBridge, load_index_html


_WEBVIEW_LOCALIZATION = {
    "global.quitConfirmation": "終了しますか？",
    "global.ok": "はい",
    "global.quit": "終了",
    "global.cancel": "キャンセル",
}


def _build_bridge() -> WebAppBridge:
    ok, message = validate_database_settings()
    if ok:
        service = create_inspection_service()
        return WebAppBridge(service, AppBootstrap(startup_error=None))
    return WebAppBridge(None, AppBootstrap(startup_error=message))


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    bridge = _build_bridge()
    html = load_index_html()
    icon_path = get_window_icon_png_path()
    window = webview.create_window(
        "外観検査記録照会",
        html=html,
        js_api=bridge,
        width=1360,
        height=900,
        min_size=(1120, 760),
        confirm_close=True,
        text_select=True,
        background_color="#F2F5F7",
    )
    bridge.bind_window(window)

    def _maximize_on_load() -> None:
        try:
            window.maximize()
        except Exception:  # noqa: BLE001
            logging.getLogger(__name__).debug(
                "window maximize failed", exc_info=True
            )

    window.events.loaded += _maximize_on_load
    webview.start(
        gui="qt",
        icon=str(icon_path) if icon_path is not None else None,
        localization=_WEBVIEW_LOCALIZATION,
    )
    return 0
