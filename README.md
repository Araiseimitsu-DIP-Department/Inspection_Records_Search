# 外観検査記録照会

Microsoft Access（`.accdb` / `.mdb`）または PostgreSQL の運用データを参照し、検索・集計表示・Excel 出力を行う Windows 用デスクトップアプリです。

画面は `pywebview`、業務処理は `application/`、`services/`、`infrastructure/` に分離しています。配布版は onefile の `外観検査記録照会.exe` を想定しています。

## 主な機能

| 画面 | 内容 |
|------|------|
| 検査員集計 | 表示開始日・表示終了日・品番で明細を検索し、Excel 出力できます。 |
| ロットID集計 | 品番と工程でロットの集計結果を表示し、Excel 出力できます。 |
| 検査員別照会 | 検査員と日付範囲で明細と集計を横並び表示します。 |

Excel 出力時は保存ダイアログを開き、ユーザーが保存先とファイル名を選択します。

## DB バックエンド

`.env` の `DB_BACKEND` で切り替えます。

| 値 | 内容 |
|---|---|
| `access` | Access ファイルを直接参照します。 |
| `postgres` | PostgreSQL を参照します。PostgreSQL 側の物理名は英語表記です。 |

PostgreSQL 移行の詳細は [docs/postgresql-migration.md](docs/postgresql-migration.md) を参照してください。

## 現在の構成

```text
Inspection_Records_Search/
├─ main.py
├─ build_exe.ps1
├─ requirements.txt
├─ README.md
├─ database/
│  └─ postgresql/
│     ├─ 001_schema.sql
│     ├─ 002_indexes.sql
│     ├─ 003_constraints.sql
│     ├─ 020_validation.sql
│     └─ migration_notes.md
├─ docs/
│  ├─ postgresql-migration.md
│  ├─ 外観検査記録照会_meta.md
│  ├─ 外観検査記録照会_meta.json
│  ├─ 外観検査記録照会_ddl.sql
│  ├─ 外観検査記録照会_architecture.md
│  ├─ Form_f_表示.cls
│  ├─ Form_f_個人別照会.cls
│  ├─ VBA.txt
│  ├─ code_2.html
│  ├─ DESIGN_1.md
│  ├─ DESIGN_2.md
│  └─ 精密部品の品質検査.png
├─ scripts/
│  ├─ generate_app_ico.py
│  ├─ migrate_access_to_postgres.py
│  └─ pyinstaller_build.py
└─ src/inspection_records_search/
   ├─ app.py
   ├─ config.py
   ├─ webview_app.py
   ├─ web/
   │  └─ index.html
   ├─ application/
   │  └─ inspection_use_case.py
   ├─ infrastructure/
   │  ├─ access_gateway.py
   │  ├─ postgres_repository.py
   │  └─ repository_factory.py
   ├─ services/
   │  ├─ export_service.py
   │  └─ inspection_service.py
   ├─ domain/
   │  ├─ models.py
   │  └─ repositories.py
   └─ shared/
      └─ errors.py
```

## 処理の流れ

1. `main.py` から `inspection_records_search.app.main()` を起動します。
2. `config.py` で `.env` を読み、DB 設定を検証します。
3. `repository_factory.py` が `DB_BACKEND` に応じて Access / PostgreSQL repository を選択します。
4. `webview_app.py` が Python ブリッジを公開し、画面からの操作を `InspectionService` に渡します。
5. `web/index.html` が検索条件、一覧、確認ダイアログ、Excel 出力 UI を担います。
6. `services/export_service.py` が検索結果を `.xlsx` に出力します。

## 設定

`.env` で次の変数を使用します。

| 変数 | 説明 |
|------|------|
| `ACCESS_DB_PATH` | Access ファイルのフルパス |
| `DB_BACKEND` | `access` または `postgres` |
| `POSTGRES_CONNECTION_URL` | PostgreSQL 接続URL |
| `POSTGRES_SCHEMA` | PostgreSQL schema。通常は `public` |
| `EXPORT_DIR` | 保存ダイアログの初期フォルダ。未指定時はアプリ基準の既定フォルダ |

旧名の `DATABASE_BACKEND` / `POSTGRES_DSN` も互換で読み取れますが、新規設定では `DB_BACKEND` / `POSTGRES_CONNECTION_URL` を使用します。

### Access を使う場合

```env
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\外観検査記録照会.accdb
DB_BACKEND=access
POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/inspection_records_search
POSTGRES_SCHEMA=public
EXPORT_DIR=
```

### PostgreSQL を使う場合

```env
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\外観検査記録照会.accdb
DB_BACKEND=postgres
POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/inspection_records_search
POSTGRES_SCHEMA=public
EXPORT_DIR=
```

## PostgreSQL 移行

PostgreSQL 側のテーブル名・カラム名は英語表記です。Access の日本語物理名は、移行スクリプト内で英語名へマッピングします。

dry-run:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --dry-run
```

検証投入:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --apply-schema --truncate --indexes --constraints
```

完全移行では、利用者停止、バックアップ、dry-run、再投入、検証、アプリ確認の順に実施します。

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 開発起動

```powershell
.\.venv\Scripts\python.exe .\main.py
```

## onefile ビルド

```powershell
.\build_exe.ps1
```

ビルド結果は `dist\外観検査記録照会.exe` です。`build/` / `dist/` 配下はビルド途中で生成される中間成果物で、配布対象ではありません。

## アイコン

- デスクトップアイコンとタスクバーアイコンの元画像: `docs/精密部品の品質検査.png`
- ビルド時にこの PNG から Windows 用 `.ico` を生成して exe に埋め込みます。

## 補足

- 画面は `pywebview` の Edge WebView2 バックエンドを使います。実行PCに WebView2 ランタイムが必要です。
- 配布版は onefile のため、実行時に別途 Python を入れる必要はありません。
- Access / ODBC / PostgreSQL の接続可否は利用環境に依存します。
