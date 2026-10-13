# AIハーネス・PostgreSQLビルド最適化の検証結果

2026-10-13。指定の既存プロジェクトAIハーネス手順とcreate-harnessの共通参照を読み、調査・設計・生成・自己レビューを実施。
目的はAccessコードを保持したままPostgreSQL運用の依存を分離すること。照会SQL・集計仕様は変更していない。

## 変更ファイル

| 区分 | ファイル |
|---|---|
| ビルド・依存 | `build_exe.ps1`、`scripts/pyinstaller_build.py`、`requirements.txt`、追加`requirements-access.txt` |
| 構成・起動説明 | `.env.example`、`.gitignore`、`main.py`、`src/inspection_records_search/config.py` |
| 依存境界 | `infrastructure/repository_factory.py`、`infrastructure/access_gateway.py`、`infrastructure/postgres_repository.py`、`services/inspection_service.py`、追加`domain/process_options.py`（すべて`src/inspection_records_search/`配下） |
| 検証 | 追加`scripts/verify_build.py`、`scripts/smoke_postgres.py`、`tests/test_runtime_profile.py` |
| ハーネスの地図・制約 | 追加`AGENTS.md`、`.cursor/rules/development.mdc`、`.cursor/rules/safety.mdc` |
| ハーネス手順 | 追加`.agents/skills/`のdevelopment-workflow、implement-feature、fix-bug、review-code、release、database-backend-buildの各SKILL.md |
| 共通参照 | 追加`.agents/skills/development-workflow/references/data-update-verification.md`、`learning-feedback.md`（指定templatesから配置） |
| Docs | `README.md`、`docs/postgresql-migration.md`、追加`docs/ARCHITECTURE.md`、`BUSINESS_RULES.md`、`DATABASE.md`、`RELEASE.md`、`update.md`、本報告 |
| 自動生成 | PostgreSQL用ルート`.spec`、Access用`build/access/`の`.spec`、各exe（Git管理外） |

直前の検査員候補修正で変更済みだった`web/index.html`と`webview_app.py`は保持し、今回のビルドへ含めた。
templates自体、開発用の元`.env`、本番データ、DBスキーマは変更していない。

## 除外・保持

PostgreSQL版からpyodbc拡張、pypyodbc、win32com、Accessリポジトリ、ACCESS_DB_PATHを除外。
Access DBファイル、移行スクリプト、SQL、Tests、ハーネスは同梱対象外。pypyodbc / win32comの実利用は調査で見つからなかった。
Access接続・SQL・リポジトリ・各移行スクリプトはソースに保持。共通工程定義を移動し旧Access import先でも再exportする。
PostgreSQL版起動でAccess専用モジュールを読み込まず、Access指定は設定エラーで停止する。Accessへの自動フォールバックはない。
psycopg / binary / libpq、pywebview / WinForms / WebView2 / clr、openpyxl、dotenv、アイコン・HTML・ロゴは維持。
OSにインストールされたODBCドライバーは変更していない。

## Verification Report

| 項目 | 結果・範囲 |
|---|---|
| Tests | PASS: unittest 9件。既存4件と新規5件 |
| Syntax | PASS: compileall（src / scripts / tests） |
| Lint | NOT RUN: 既存ツール設定なし |
| Type Check | NOT RUN: 既存ツール設定なし |
| Startup | PASS（ソース起動経路）: Access importを禁止した新規プロセスでサービス生成、HTML、Edge指定を確認。GUIはモック |
| Functional Check | PASS: 実PostgreSQL、読み取り専用・タイムアウト付き。2026-10-13は明細0件、2026-10-05は明細3件。両日でマスタ・検査員集計明細・検査員別明細/集計・対象品番ロット集計・一時Excel読み戻し成功 |
| Build | PASS: PostgreSQL版とAccess対応版、両exe内部のモジュール・バイナリ・必須資源・設定監査 |
| Access preservation | PASS: git HEADとのAST比較でAccess接続・SQL・リポジトリメソッド、共通照合処理を保持 |
| PostgreSQL preservation | PASS: importを除いたモジュールASTがgit HEADと一致 |
| Skills | PASS: 配置後6スキルのquick_validate、ハーネス関連14ファイルの相対リンク検査。重複・役割・未確定事項の混入を自己レビュー |
| Git Diff / Status | CHECKED: diff --check成功、既存変更保持と新規ファイルを確認 |
| Review | Critical / Highの指摘なし。未確認項目は以下に明記 |
| Release Ready | NO（本番配布判断保留）: 実exeのGUI・配布先PCの検証が未実施 |

データ更新の共通検証は、今回変更したDB処理に書き込みがないため移行・再投入・再実行の試験は適用外。
Excel smokeは一時ファイルへ保存して読み戻し、件数・見出しを検査した。本番ファイルの更新は行っていない。
スキル検証用PyYAMLは`build/harness-validator`だけに導入し、exeに入っていないことを確認した。

## サイズ

| 成果物 | バイト |
|---|---:|
| 変更前の通常exe | 25,279,236 |
| 変更後のPostgreSQL専用exe | 25,216,995 |
| 削減量 | 62,241（約0.246%） |
| Access対応版exe | 25,280,768 |

サイズ削減は小さいが、専用依存の除外と復帰可能な構成を優先した。

## 残存確認事項

- 実exeのGUI、3画面の操作、候補スクロール、Excel保存ダイアログ、配布先PCのWebView2 / .NETは未検証。
- Access実接続とODBCドライバー、復帰時のデータ同期は未検証。Access版のビルドと内部構成まで確認。
- 実DB smokeは2日・1名・対象品番のサンプルで、全期間やAccess結果との全件一致は未確認。
- 共通エラー表示のAccess向け文言は残存。今回のビルド分離の範囲では変更していない。
- 実データ投入、移行再実行、バックアップ復旧、本番配布は実施していない。

次の確認は配布予定PCでPostgreSQL専用exeを開き、3画面と保存操作を確認すること。Access復帰が必要なら別成果物とODBC環境を確認する。
