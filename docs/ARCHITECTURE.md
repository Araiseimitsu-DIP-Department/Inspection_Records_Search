# 構造と調査結果

## Confirmed

2026-10-13、ソース、README、設定例、既存テスト、ビルドスクリプトを調査した。
目的は外観検査記録の検索・集計・Excel出力。画面は検査員集計、ロットID集計、検査員別照会。

| 領域 | 主なファイル・役割 |
|---|---|
| 起動 | `main.py` → `src/inspection_records_search/app.py` |
| 設定 | `config.py`: .env、バックエンド選択、同梱資源のパス |
| UI | `web/index.html`: HTML/CSS/JavaScript、`webview_app.py`: pywebview JSブリッジ |
| 業務入口 | `services/inspection_service.py` → `application/inspection_use_case.py` |
| DB | `infrastructure/repository_factory.py`、PostgreSQL / Accessリポジトリ |
| 共通 | `domain/models.py`、`domain/process_options.py`、`shared/errors.py` |
| Excel | `services/export_service.py`: openpyxlによるローカルファイル保存 |
| ビルド | `build_exe.ps1` → `scripts/pyinstaller_build.py` → PyInstaller onefile |
| 移行 | `scripts/migrate_access_to_postgres.py`、`database/postgresql/`、既存移行Docs |

Python、pywebview、Edge WebView2、pythonnet、python-dotenv、psycopg binary、openpyxl、Pillowを使用する。
外部接続はPostgreSQLの2つのDBまたはAccessファイル。リモートHTTP APIの実装は確認されていない。UIからPythonへはローカルJSブリッジを使う。
環境変数の一覧はREADMEを参照。`.env`はGit対象外。`POSTGRES_SCHEMA`は設定例・移行処理に存在するが、通常アプリの照会SQLではテーブル名を修飾していない。
CHANGELOG、lint、型チェックの既存設定は調査時に見つからなかった。履歴は今回追加した`update.md`を使用する。

## 調査時の矛盾と対応

- ユーザー指定の現在運用はPostgreSQLだが、設定例・設定未指定時の既定値はAccessだった。設定例をPostgreSQLへ変更。開発時の既存既定値は保持し、凍結版は同梱プロファイルを既定値とする。
- PostgreSQL実装・サービスがAccessモジュールの工程定義をimportし、pyodbcが起動時に必要だった。値と照合処理を変更せず共通モジュールへ移動した。
- 移行Docsの「.envをAccessに戻す」は従来の両対応版を前提としていた。今回のPostgreSQL専用exeではAccess対応版の再ビルドも必要。
- 共通エラー表示にはAccess向け文言が残っている。今回の依存分離では変更していない。

## Assumption

業務仕様を推測して追加した内容はない。テストで確認できた処理と実運用の期待値が完全一致するかは、担当者による確認が必要。

## Unknown / Human Validation Required

- 配布先PCのWebView2 / .NET環境、正式な配布先・配布手順。
- 実DBの全期間・全データとAccess画面の完全な結果一致。
- Accessへ復帰する時点のデータ同期方針・ODBCドライバー環境。
- 運用アカウントの権限、バックアップ復旧手順、リリース承認者。

## ハーネス設計

AGENTSは参照地図、Rulesは制約、Skillsは手順、Docsは仕様、Testsは検証、update.mdは履歴に限定する。
固有Skillは繰り返すバックエンド切替と成果物監査を扱う`database-backend-build`に限定した。
移行・Excel出力は既存Docsとデータ更新の共通手順で扱うため、専用Skillを追加していない。

| Skill | 使用時・役割 | 主な参照Docs / Tests |
|---|---|---|
| development-workflow | 作業分類・他Skillへの入口 | AGENTS、RELEASE / 変更に関係するTests |
| implement-feature | 機能の追加・変更 | ARCHITECTURE、BUSINESS_RULES、DATABASE / 対象仕様のTests |
| fix-bug | 再現・原因調査・最小修正 | ARCHITECTURE、BUSINESS_RULES / 発生経路の回帰Tests |
| review-code | 実装結果の評価 | BUSINESS_RULES、DATABASE / 変更に関係するTestsと実施結果 |
| release | 配布前の検証と未確認事項の整理 | RELEASE、README、更新履歴 / 全unittest・成果物検査 |
| database-backend-build | バックエンド依存・成果物境界 | DATABASE、RELEASE / test_runtime_profile、test_postgres_repository、verify_build |
