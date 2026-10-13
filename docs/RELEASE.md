# ビルド構成と検証

## 成果物

通常の`build_exe.ps1`はPostgreSQL専用onefile exeを`dist/外観検査記録照会.exe`へ生成する。
Access対応版は`build_exe.ps1 -Backend access`で`dist/access/外観検査記録照会.exe`へ生成し、PostgreSQL版を上書きしない。
ビルド途中のファイルは`build/postgres`と`build/access`へ分離する。`.spec`はビルドスクリプトによる自動生成物で、構成の管理元はPythonビルドスクリプト。

PostgreSQL版はAccessリポジトリ、pyodbc、pypyodbc、win32comを収集しない。Access DBファイル、移行スクリプト、SQL、テスト、ハーネスDocsは同梱対象にしていない。
HTML、アイコン、ロゴ、WebView2 / WinForms関連資源、PostgreSQL・Excel依存は維持する。

同梱`.env`はPostgreSQL接続・数量DB接続・schema・出力先の既知キーだけを保持し、DB_BACKENDをpostgresとする。ACCESS_DB_PATHとAccess別名設定は除外する。開発用の元`.env`は書き換えない。
exe横の`.env`は従来どおり同梱値を上書きする。ただしPostgreSQL専用版でAccessを指定した場合は設定エラーを表示する。
設定未指定時は凍結版の同梱プロファイルを採用し、開発時の旧既定値accessは保持する。
接続情報を含むexeの配布範囲は人間が確認する。

## Verification Gate

プロジェクトルートで実行する。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q src scripts tests
.\build_exe.ps1
.\.venv\Scripts\python.exe scripts\verify_build.py dist\外観検査記録照会.exe
# 実DBの読み取りが可能な場合のみ（全接続でread-only、接続・SQLタイムアウト付き）
.\.venv\Scripts\python.exe scripts\smoke_postgres.py --date 2026-10-13
git diff --check
git diff
git status --short
```

`verify_build.py`はexe内部のPYZとバイナリ・資源を読み取り、専用依存の不在、必要なUI/DB/Excel資源の存在、バックエンドマーカー、同梱設定を検査する。ビルドスクリプトからも自動実行する。
起動テストはAccess importを禁止した新規Pythonプロセスで、サービス生成、HTML読込、Edge起動指定まで確認する。ウィンドウ生成はモックであり、実exeのGUI確認を代替しない。
smokeは当日の明細、氏名のある検査員1名の照会、明細中の品番（該当なしなら存在しない試験値）のロット集計と一時Excelの読み戻しを行う。全件照合ではない。

lint / 型チェックツールは未導入のためNOT RUNとする。Tests、Startup、Functional Check、Build、Git Diff、Git StatusをPASS / FAIL / NOT RUNで報告し、未実施は理由を示す。
実exeの3画面・候補スクロール・保存ダイアログ・配布先PCのWebView2は人間確認。未確認なら本番配布可能と断定しない。

## Access復帰と配布

Access復帰には`requirements-access.txt`、Access対応exe、対象PCのMicrosoft Access ODBCドライバー、Access DBパスが必要。設定切替だけでPostgreSQL専用exeへAccess依存を追加することはできない。
移行ツール実行にはAccess追加依存を導入する。データ同期・ロールバックは既存移行Docsの確認事項に従う。
exe生成は本番配布ではない。配布・本番設定変更はRulesのApproval Gateに従う。
