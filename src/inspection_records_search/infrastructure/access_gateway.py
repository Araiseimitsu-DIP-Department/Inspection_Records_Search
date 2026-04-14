"""Access（pyodbc）接続と Access 実装リポジトリ。"""

from __future__ import annotations

import datetime as dt
from contextlib import contextmanager
from typing import Iterator, Optional

import pyodbc

from inspection_records_search.shared.errors import (
    DataConversionError,
    DataIntegrityError,
    DatabaseQueryError,
    DatabaseUnavailableError,
)


def build_connection_string(db_path: str) -> str:
    # 日本語パス・UNC 対策で DBQ はそのまま渡す（ドライバが解釈）
    return (
        r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
        f"DBQ={db_path};"
    )


@contextmanager
def access_connection(db_path: str) -> Iterator[pyodbc.Connection]:
    conn_str = build_connection_string(db_path)
    conn = pyodbc.connect(conn_str, autocommit=True)
    try:
        yield conn
    finally:
        conn.close()


def execute_query(
    db_path: str, sql: str, params: tuple | list | None = None
) -> tuple[list[str], list[tuple]]:
    """SELECT を実行し、列名と行のリストを返す。"""
    params = params or ()
    try:
        with access_connection(db_path) as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            columns = [c[0] for c in cur.description] if cur.description else []
            rows = cur.fetchall()
            return columns, [tuple(r) for r in rows]
    except pyodbc.DataError as e:
        raise DataConversionError(str(e)) from e
    except pyodbc.IntegrityError as e:
        raise DataIntegrityError(str(e)) from e
    except pyodbc.OperationalError as e:
        raise DatabaseUnavailableError(str(e)) from e
    except pyodbc.InterfaceError as e:
        raise DatabaseUnavailableError(str(e)) from e
    except pyodbc.Error as e:
        raise DatabaseQueryError(str(e)) from e


# The repository keeps Access SQL here so the UI/application layers stay database-agnostic.
DEFAULT_KOUTEI_FALLBACK: tuple[str, ...] = (
    "バリ取り",
    "ゲージ検査",
    "エアー吹き",
    "切粉除去",
    "返品再検査",
    "マイクロ検",
    "仕掛再検査",
    "ボッチ取り",
    "在庫再検査",
    "トレー詰め",
)

_KOUTEI_CODE_NAME: tuple[tuple[str, str], ...] = (
    ("15", "バリ取り"),
    ("16", "ゲージ検査"),
    ("17", "エアー吹き"),
    ("18", "切粉除去"),
    ("19", "返品再検査"),
    ("20", "マイクロ検"),
    ("21", "仕掛再検査"),
    ("22", "ボッチ取り"),
    ("23", "在庫再検査"),
    ("24", "トレー詰め"),
)


def _expand_koutei_match_values(raw: str) -> list[str]:
    """工程NO 条件に、コードと名称の両方を含める。"""
    t = raw.strip()
    if not t:
        return []
    out: list[str] = []
    seen: set[str] = set()

    def add(v: str) -> None:
        if v and v not in seen:
            seen.add(v)
            out.append(v)

    add(t)
    for code, name in _KOUTEI_CODE_NAME:
        if t == code:
            add(name)
        elif t == name:
            add(code)
    return out


class AccessInspectionRepository:
    """Access DB に閉じた concrete repository."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    @property
    def db_path(self) -> str:
        return self._db_path

    def fetch_inspectors(self) -> tuple[list[str], list[tuple]]:
        sql = (
            "SELECT 検査員ID, 検査員名 FROM t_検査員マスタ "
            "ORDER BY 検査員ID"
        )
        return execute_query(self._db_path, sql)

    def fetch_personal_records(
        self,
        inspector_id: str,
        date_from: dt.date,
        date_to: dt.date,
    ) -> tuple[list[str], list[tuple]]:
        sql = (
            "SELECT 検査員ID, 生産ロットID, 工程NO, 日付, 時刻, 品番, 品名, 客先 "
            "FROM t_外観検査記録 "
            "WHERE 検査員ID = ? AND 日付 >= ? AND 日付 <= ? "
            "ORDER BY 日付, 時刻"
        )
        return execute_query(
            self._db_path, sql, [inspector_id, date_from, date_to]
        )

    def fetch_personal_summary(
        self,
        inspector_id: str,
        date_from: dt.date,
        date_to: dt.date,
    ) -> tuple[list[str], list[tuple]]:
        sql = (
            "SELECT 検査員ID, 生産ロットID, 工程NO, 日付, 品番, 品名, 数量, 作業時間 "
            "FROM t_外観検査集計 "
            "WHERE 検査員ID = ? AND 日付 >= ? AND 日付 <= ? "
            "ORDER BY 日付, ID"
        )
        return execute_query(
            self._db_path, sql, [inspector_id, date_from, date_to]
        )

    def fetch_main_detail(
        self,
        date_from: dt.date,
        date_to: dt.date,
        part_number: Optional[str],
    ) -> tuple[list[str], list[tuple]]:
        col = "t_外観検査集計.日付"
        sql = (
            "SELECT t_外観検査集計.ID, t_外観検査集計.検査員ID, t_検査員マスタ.検査員名, "
            "t_外観検査集計.日付, t_外観検査集計.生産ロットID, "
            "t_外観検査集計.品番, t_外観検査集計.品名, t_外観検査集計.工程NO, "
            "t_外観検査集計.数量, t_外観検査集計.作業時間, t_外観検査集計.集計除外フラグ, "
            "t_数値検査員マスタ.検査員名 AS 数値検査員名 "
            "FROM ((t_外観検査集計 "
            "LEFT JOIN t_検査員マスタ ON t_外観検査集計.検査員ID = t_検査員マスタ.検査員ID) "
            "LEFT JOIN t_数値検査記録 ON t_外観検査集計.生産ロットID = t_数値検査記録.生産ロットID) "
            "LEFT JOIN t_数値検査員マスタ ON t_数値検査記録.検査員ID = t_数値検査員マスタ.検査員ID "
            f"WHERE {col} >= ? AND {col} <= ?"
        )
        params: list[object] = [date_from, date_to]
        if part_number and part_number.strip():
            sql += " AND t_外観検査集計.品番 = ?"
            params.append(part_number.strip())
        sql += (
            " ORDER BY t_外観検査集計.日付, t_外観検査集計.検査員ID, t_外観検査集計.ID"
        )
        return execute_query(self._db_path, sql, params)

    def fetch_koutei_distinct_values(self) -> list[str]:
        sql_candidates = (
            "SELECT DISTINCT 工程NO FROM Q_生産ロット集計 "
            "WHERE Len(Trim(Nz([工程NO],'')))>0 ORDER BY 工程NO",
            "SELECT DISTINCT 工程NO FROM t_外観検査集計 "
            "WHERE Len(Trim(Nz([工程NO],'')))>0 ORDER BY 工程NO",
            "SELECT DISTINCT 工程NO FROM t_外観検査記録 "
            "WHERE Len(Trim(Nz([工程NO],'')))>0 ORDER BY 工程NO",
        )
        for sql in sql_candidates:
            try:
                headers, rows = execute_query(self._db_path, sql)
                if not headers:
                    continue
                out: list[str] = []
                seen: set[str] = set()
                for r in rows:
                    if not r:
                        continue
                    v = r[0]
                    if v is None:
                        continue
                    s = str(v).strip()
                    if not s or s in seen:
                        continue
                    seen.add(s)
                    out.append(s)
                if out:
                    return out
            except Exception:
                continue
        return []

    def fetch_lot_aggregate(
        self,
        hinban: Optional[str],
        koutei: Optional[str],
    ) -> tuple[list[str], list[tuple]]:
        sql = (
            "SELECT 生産ロットID, 工程NO, 品番, 品名, 数量, 作業時間の合計 "
            "FROM Q_生産ロット集計"
        )
        wheres: list[str] = []
        params: list[object] = []
        if hinban and hinban.strip():
            wheres.append("品番 = ?")
            params.append(hinban.strip())
        if koutei and koutei.strip():
            k_vars = _expand_koutei_match_values(koutei)
            if len(k_vars) == 1:
                wheres.append("工程NO = ?")
                params.append(k_vars[0])
            else:
                wheres.append("(" + " OR ".join(["工程NO = ?"] * len(k_vars)) + ")")
                params.extend(k_vars)
        if wheres:
            sql += " WHERE " + " AND ".join(wheres)
        sql += " ORDER BY 生産ロットID, 工程NO"
        return execute_query(self._db_path, sql, params)

