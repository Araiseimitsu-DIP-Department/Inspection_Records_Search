# DBと依存関係

## データアクセス

通常アプリはSELECTのみを発行する。PostgreSQLの本体は`appearance_inspection_db`、数量・数値検査履歴は`delivery_label_db`。
テーブル定義は`database/postgresql/001_schema.sql`、移行対応は[既存移行Docs](postgresql-migration.md)を参照する。
PostgreSQL接続はpsycopgで明示的にcloseし、接続失敗時にAccessへフォールバックする処理はない。
SQLの検索条件はパラメータとして渡す。通常アプリの表名は未修飾のため、接続先のsearch_pathに依存する。

## 依存の分類

| 区分 | 実装・依存 | ビルドでの扱い |
|---|---|---|
| Access専用 | `access_gateway.py`、pyodbc、Microsoft Access ODBCドライバー | ソースを保持、PostgreSQL成果物から除外 |
| PostgreSQL専用 | `postgres_repository.py`、psycopg、psycopg_binary / libpq | 維持 |
| 共通業務 | `domain/process_options.py`、UseCase、DTO、共通例外 | 維持 |
| 共通UI・出力 | pywebview、pythonnet / clr、WebView2資源、dotenv、openpyxl、Pillow | 維持 |
| 未使用のAccess候補 | pypyodbc、win32com | 利用箇所なし。PostgreSQLビルドでは収集禁止 |

OSのODBCドライバーをアンインストールする処理はない。旧成果物にもAccess ODBCドライバー自体は含まれておらず、pyodbcの拡張モジュールとAccessリポジトリが含まれていた。
`access_gateway.py`は共通定義を再exportするため、旧import先の互換性を保つ。
`requirements.txt`は通常運用用、`requirements-access.txt`は共通依存にpyodbcを追加する。

## 更新境界

`export_service.py`はExcelファイルを書き込む。`scripts/migrate_access_to_postgres.py`はDDL・投入・TRUNCATE・commitを実行する別ツール。
`docs/appearance_inspection_db/`と`docs/delivery_label_search_db/`にもpyodbcを使用する既存移行スクリプトがある。ソースを保持し、通常exeには同梱しない。
移行ツールはテーブル単位でcommitし、全移行の一括ロールバックを保証していない。`--dry-run`はAccess件数を読む方式で、PostgreSQLの変更計画全体を検証する機能ではない。
今回のビルド変更では移行処理を実行せず、投入・削除・スキーマ変更も行わない。
