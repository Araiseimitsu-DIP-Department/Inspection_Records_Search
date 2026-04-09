"""Access（pyodbc）接続。"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import pyodbc


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
    with access_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        columns = [c[0] for c in cur.description] if cur.description else []
        rows = cur.fetchall()
        return columns, [tuple(r) for r in rows]
