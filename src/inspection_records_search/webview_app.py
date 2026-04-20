"""pywebview bridge and bootstrap helpers for the inspection inquiry app."""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import webview
from inspection_records_search.services.export_service import export_to_xlsx
from inspection_records_search.services.inspection_service import (
    DEFAULT_KOUTEI_FALLBACK,
    InspectionService,
)
from inspection_records_search.shared.errors import describe_exception

_LOG = logging.getLogger(__name__)

_APP_TITLE = "外観検査記録照会"
_APP_SUBTITLE = "検索・集計・Excel出力"

_KOUTEI_CODE_NAME: tuple[tuple[str, str], ...] = (
    ("15", "バリ取り"),
    ("16", "ゲージ検査"),
    ("17", "エアー吹き"),
    ("18", "切粉除去"),
    ("19", "返品再検査"),
    ("20", "マイクロ検"),
    ("21", "仕掛再検査"),
    ("22", "ポッチ取り"),
    ("23", "在庫再検査"),
    ("24", "トレー詰め"),
)


def _today_iso() -> str:
    return dt.date.today().isoformat()


def _is_date_header(header: str) -> bool:
    return any(token in header for token in ("日付", "日", "年月日"))


def _is_time_header(header: str) -> bool:
    return any(token in header for token in ("時刻", "時間", "時"))


def _parse_loose_date_string(text: str) -> dt.date | None:
    raw = text.strip()
    if not raw:
        return None
    candidates = [raw]
    if " " in raw:
      candidates.append(raw.split(" ", 1)[0])
    if "T" in raw:
      candidates.append(raw.split("T", 1)[0])
    for candidate in candidates:
        normalized = candidate.replace("/", "-").replace(".", "-")
        try:
            return dt.date.fromisoformat(normalized)
        except ValueError:
            continue
    return None


def _parse_loose_time_string(text: str) -> dt.time | None:
    raw = text.strip()
    if not raw:
        return None
    if " " in raw:
        raw = raw.split(" ", 1)[-1]
    if "T" in raw:
        raw = raw.split("T", 1)[-1]
    raw = raw.strip()
    if not raw:
        return None
    try:
        return dt.time.fromisoformat(raw)
    except ValueError:
        pass
    if ":" in raw:
        parts = raw.split(":")
        if len(parts) >= 2:
            try:
                hour = int(parts[0])
                minute = int(parts[1])
                second = int(parts[2]) if len(parts) >= 3 else 0
                return dt.time(hour, minute, second)
            except ValueError:
                return None
    return None


def _display_value(value: Any, header: str = "") -> str:
    if value is None:
        return ""
    if isinstance(value, dt.datetime):
        if _is_date_header(header):
            return value.strftime("%Y/%m/%d")
        if _is_time_header(header):
            return f"{value.hour}:{value.minute:02d}"
        return value.strftime("%Y/%m/%d %H:%M")
    if isinstance(value, dt.date):
        return value.strftime("%Y/%m/%d")
    if isinstance(value, dt.time):
        return f"{value.hour}:{value.minute:02d}"
    if isinstance(value, str):
        if _is_date_header(header):
            parsed_date = _parse_loose_date_string(value)
            if parsed_date is not None:
                return parsed_date.strftime("%Y/%m/%d")
        if _is_time_header(header):
            parsed_time = _parse_loose_time_string(value)
            if parsed_time is not None:
                return f"{parsed_time.hour}:{parsed_time.minute:02d}"
            return value.strip()
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return str(value)


def _serialize_cell(value: Any, header: str = "") -> dict[str, Any]:
    if value is None:
        return {"kind": "null", "value": None, "display": ""}
    if isinstance(value, dt.datetime):
        return {
            "kind": "datetime",
            "value": value.isoformat(),
            "display": _display_value(value, header),
        }
    if isinstance(value, dt.date):
        return {
            "kind": "date",
            "value": value.isoformat(),
            "display": _display_value(value, header),
        }
    if isinstance(value, dt.time):
        return {
            "kind": "time",
            "value": value.isoformat(),
            "display": _display_value(value, header),
        }
    if isinstance(value, Decimal):
        return {
            "kind": "decimal",
            "value": str(value),
            "display": _display_value(value, header),
        }
    if isinstance(value, bytes):
        text = value.decode(errors="replace")
        return {"kind": "bytes", "value": text, "display": text}
    if isinstance(value, bool):
        return {"kind": "bool", "value": value, "display": "1" if value else "0"}
    if isinstance(value, int):
        return {"kind": "int", "value": value, "display": str(value)}
    if isinstance(value, float):
        return {"kind": "float", "value": value, "display": str(value)}
    return {"kind": "text", "value": str(value), "display": _display_value(value, header)}


def _restore_cell(cell: Any) -> Any:
    if not isinstance(cell, dict):
        return cell
    kind = cell.get("kind")
    value = cell.get("value")
    if kind == "null":
        return None
    if kind == "date" and value:
        return dt.date.fromisoformat(str(value))
    if kind == "datetime" and value:
        return dt.datetime.fromisoformat(str(value))
    if kind == "time" and value:
        return dt.time.fromisoformat(str(value))
    if kind == "decimal" and value is not None:
        return Decimal(str(value))
    if kind == "bool":
        return bool(value)
    if kind == "int" and value is not None:
        return int(value)
    if kind == "float" and value is not None:
        return float(value)
    return value


def _serialize_table(
    headers: list[str],
    rows: list[tuple],
    *,
    hidden_headers: list[str] | None = None,
) -> dict[str, Any]:
    hidden_headers = hidden_headers or []
    hidden_columns = [
        idx for idx, header in enumerate(headers) if header in hidden_headers
    ]
    return {
        "headers": list(headers),
        "hidden_columns": hidden_columns,
        "rows": [
            [_serialize_cell(value, header) for header, value in zip(headers, row)]
            for row in rows
        ],
    }


def _table_error(exc: BaseException) -> dict[str, Any]:
    _LOG.exception("webview operation failed")
    if isinstance(exc, ValueError):
        message = str(exc)
    else:
        message = describe_exception(exc)
    return {"ok": False, "error": message}


def _ok(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"ok": True}
    if payload:
        out.update(payload)
    return out


@dataclass(slots=True)
class AppBootstrap:
    startup_error: str | None


class WebAppBridge:
    """Python bridge exposed to the frontend."""

    def __init__(
        self,
        service: InspectionService | None,
        bootstrap: AppBootstrap,
    ) -> None:
        self._svc = service
        self._bootstrap = bootstrap
        self._window: webview.Window | None = None

    def bind_window(self, window: webview.Window) -> None:
        self._window = window

    def bootstrap(self) -> dict[str, Any]:
        if self._bootstrap.startup_error is not None:
            return _ok(
                {
                    "app": {
                        "title": _APP_TITLE,
                        "subtitle": _APP_SUBTITLE,
                    },
                    "today": _today_iso(),
                    "startup_error": self._bootstrap.startup_error,
                    "inspectors": [],
                    "koutei_options": list(DEFAULT_KOUTEI_FALLBACK),
                }
            )

        if self._svc is None:
            return _ok(
                {
                    "app": {
                        "title": _APP_TITLE,
                        "subtitle": _APP_SUBTITLE,
                    },
                    "today": _today_iso(),
                    "startup_error": "アプリの初期化に失敗しました。",
                    "inspectors": [],
                    "koutei_options": list(DEFAULT_KOUTEI_FALLBACK),
                }
            )

        try:
            inspectors = self._load_inspectors()
        except Exception:  # noqa: BLE001
            _LOG.exception("failed to preload inspectors")
            inspectors = []
        try:
            koutei_options = self._load_koutei_options()
        except Exception:  # noqa: BLE001
            _LOG.exception("failed to preload koutei options")
            koutei_options = list(DEFAULT_KOUTEI_FALLBACK)
        return _ok(
            {
                "app": {
                    "title": _APP_TITLE,
                    "subtitle": _APP_SUBTITLE,
                },
                "today": _today_iso(),
                "startup_error": None,
                "inspectors": inspectors,
                "koutei_options": koutei_options,
                "koutei_pairs": self._load_koutei_pairs(),
            }
        )

    def fetch_inspectors(self) -> dict[str, Any]:
        try:
            return _ok({"inspectors": self._load_inspectors()})
        except Exception as exc:  # noqa: BLE001
            return _table_error(exc)

    def fetch_koutei_options(self) -> dict[str, Any]:
        try:
            return _ok({"koutei_options": self._load_koutei_options()})
        except Exception as exc:  # noqa: BLE001
            return _table_error(exc)

    def search_main_detail(
        self,
        date_from: str,
        date_to: str,
        part_number: str | None = None,
    ) -> dict[str, Any]:
        try:
            if self._svc is None:
                raise RuntimeError("Service is unavailable.")
            d0 = dt.date.fromisoformat(date_from)
            d1 = dt.date.fromisoformat(date_to)
            headers, rows = self._svc.fetch_main_detail(
                d0,
                d1,
                (part_number or "").strip() or None,
            )
            return _ok(
                {
                    "table": _serialize_table(
                        headers,
                        rows,
                        hidden_headers=["ID", "集計除外フラグ", "検査取消フラグ"],
                    )
                }
            )
        except Exception as exc:  # noqa: BLE001
            return _table_error(exc)

    def search_lot_aggregate(
        self,
        part_number: str | None = None,
        process_value: str | None = None,
    ) -> dict[str, Any]:
        try:
            if self._svc is None:
                raise RuntimeError("Service is unavailable.")
            headers, rows = self._svc.fetch_lot_aggregate(
                (part_number or "").strip() or None,
                (process_value or "").strip() or None,
            )
            return _ok({"table": _serialize_table(headers, rows)})
        except Exception as exc:  # noqa: BLE001
            return _table_error(exc)

    def search_personal_inquiry(
        self,
        inspector_id: str,
        date_from: str,
        date_to: str,
    ) -> dict[str, Any]:
        try:
            if self._svc is None:
                raise RuntimeError("Service is unavailable.")
            d0 = dt.date.fromisoformat(date_from)
            d1 = dt.date.fromisoformat(date_to)
            inspector_id = inspector_id.strip()
            if not inspector_id:
                raise ValueError("検査員を選択してください。")
            records_headers, records_rows = self._svc.fetch_personal_records(
                inspector_id,
                d0,
                d1,
            )
            summary_headers, summary_rows = self._svc.fetch_personal_summary(
                inspector_id,
                d0,
                d1,
            )
            return _ok(
                {
                    "records": _serialize_table(
                        records_headers,
                        records_rows,
                        hidden_headers=["検査員ID"],
                    ),
                    "summary": _serialize_table(
                        summary_headers,
                        summary_rows,
                        hidden_headers=["検査員ID"],
                    ),
                }
            )
        except Exception as exc:  # noqa: BLE001
            return _table_error(exc)

    def export_table(
        self,
        filename: str,
        headers: list[str],
        rows: list[list[Any]],
    ) -> dict[str, Any]:
        try:
            if self._svc is None:
                raise RuntimeError("Service is unavailable.")
            restored_rows = [
                tuple(_restore_cell(cell) for cell in row)
                for row in rows
            ]
            out_path = export_to_xlsx(
                None,
                filename,
                headers,
                restored_rows,
                output_dir=self._svc.export_directory,
            )
            return _ok({"path": str(out_path)})
        except Exception as exc:  # noqa: BLE001
            return _table_error(exc)

    def close_app(self) -> dict[str, Any]:
        if self._window is not None:
            self._window.destroy()
        return _ok()

    def _load_inspectors(self) -> list[dict[str, str]]:
        if self._svc is None:
            raise RuntimeError("Service is unavailable.")
        _headers, rows = self._svc.fetch_inspectors()
        inspectors: list[dict[str, str]] = []
        for row in rows:
            if len(row) < 2:
                continue
            inspector_id = "" if row[0] is None else str(row[0]).strip()
            inspector_name = "" if row[1] is None else str(row[1]).strip()
            if not inspector_id:
                continue
            label = f"{inspector_id}  {inspector_name}".rstrip()
            inspectors.append(
                {
                    "id": inspector_id,
                    "name": inspector_name,
                    "label": label,
                }
            )
        return inspectors

    def _load_koutei_options(self) -> list[str]:
        if self._svc is None:
            raise RuntimeError("Service is unavailable.")
        options = self._svc.fetch_koutei_distinct_values()
        if not options:
            options = list(DEFAULT_KOUTEI_FALLBACK)
        return options

    def _load_koutei_pairs(self) -> list[dict[str, str]]:
        pairs: list[dict[str, str]] = []
        for code, name in _KOUTEI_CODE_NAME:
            pairs.append(
                {
                    "code": code,
                    "name": name,
                    "label": f"{code}：{name}",
                }
            )
        return pairs


def load_index_html() -> str:
    from inspection_records_search.config import get_web_index_html_path

    index_path = get_web_index_html_path()
    return index_path.read_text(encoding="utf-8")
