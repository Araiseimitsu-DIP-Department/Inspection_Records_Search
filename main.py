"""
外観検査記録照会アプリのエントリポイント。
開発時: リポジトリルートの .env に ACCESS_DB_PATH を設定して実行。
配布時: exe と同じフォルダに .env を配置する。
"""

from __future__ import annotations

import sys
from pathlib import Path

# 開発時のみ src をパスに追加（onefile ではパッケージはバンドル済み）
_ROOT = Path(__file__).resolve().parent
if not getattr(sys, "frozen", False):
    _SRC = _ROOT / "src"
    if _SRC.is_dir() and str(_SRC) not in sys.path:
        sys.path.insert(0, str(_SRC))

from inspection_records_search.app import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
