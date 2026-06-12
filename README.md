# 外観検査記録照会

Access または PostgreSQL の外観検査データを参照し、検索結果の表示と Excel 出力を行う Windows 用デスクトップアプリです。
画面は `pywebview`、業務処理は `application/`、`services/`、`infrastructure/` に分離しています。

## 主な機能

| 画面 | 内容 |
|---|---|
| 検査員集計 | 表示開始日、表示終了日、品番で明細を検索し、Excel 出力できます。 |
| ロットID集計 | 品番と工程で生産ロット別の数量、作業時間を表示し、Excel 出力できます。 |
| 検査員別照会 | 検査員と期間で、検査員別明細と検査員別集計を横並びで確認できます。 |

数量は画面表示で `1,234` のようにカンマ区切りにします。Excel 出力では数値として扱えるよう、元データの値を出力します。

## DBバックエンド

`.env` の `DB_BACKEND` で切り替えます。

| 値 | 内容 |
|---|---|
| `access` | Access ファイルを直接参照します。 |
| `postgres` | PostgreSQL を参照します。 |

PostgreSQL では次の2つのデータベースを使います。

| データベース | 用途 |
|---|---|
| `appearance_inspection_db` | 外観検査記録、集計、検査員、工程マスタなどの本体データ |
| `delivery_label_search_db` | ロットID集計の数量参照用データ |

ロットID集計は Access のクエリを PostgreSQL view として作らず、Python 側で処理します。
`appearance_inspection_summaries.work_time` を集計し、数量は `delivery_label_search_db.delivery_label_search.quantity` から取得します。

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
│     ├─ delivery_label_search_schema.sql
│     └─ migration_notes.md
├─ docs/
│  ├─ postgresql-migration.md
│  ├─ appearance_inspection_db/
│  └─ delivery_label_search_db/
├─ scripts/
│  ├─ generate_app_ico.py
│  ├─ migrate_access_to_postgres.py
│  └─ pyinstaller_build.py
└─ src/inspection_records_search/
   ├─ app.py
   ├─ config.py
   ├─ webview_app.py
   ├─ web/index.html
   ├─ application/
   ├─ infrastructure/
   ├─ services/
   ├─ domain/
   └─ shared/
```

## 設定

`.env` で次の変数を使用します。

| 変数 | 説明 |
|---|---|
| `ACCESS_DB_PATH` | Access ファイルのフルパス |
| `DB_BACKEND` | `access` または `postgres` |
| `POSTGRES_CONNECTION_URL` | `appearance_inspection_db` への PostgreSQL 接続URL |
| `DELIVERY_LABEL_POSTGRES_CONNECTION_URL` | `delivery_label_search_db` への PostgreSQL 接続URL |
| `POSTGRES_SCHEMA` | PostgreSQL schema。通常は `public` |
| `EXPORT_DIR` | 保存ダイアログの初期フォルダ。未指定時はアプリ既定フォルダ |

互換用に `DATABASE_BACKEND`、`POSTGRES_DSN`、`DATABASE_URL`、`DELIVERY_LABEL_DATABASE_URL` も読み取れますが、新規設定では上記の変数を使用してください。

### Access を使う場合

```env
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\外観検査記録照会.accdb
DB_BACKEND=access
POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/appearance_inspection_db
DELIVERY_LABEL_POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/delivery_label_search_db
POSTGRES_SCHEMA=public
EXPORT_DIR=
```

### PostgreSQL を使う場合

```env
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\外観検査記録照会.accdb
DB_BACKEND=postgres
POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/appearance_inspection_db
DELIVERY_LABEL_POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/delivery_label_search_db
POSTGRES_SCHEMA=public
EXPORT_DIR=
```

## PostgreSQL移行

詳細は [docs/postgresql-migration.md](docs/postgresql-migration.md) を参照してください。

dry-run:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --dry-run
```

検証投入または完全再投入:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --apply-schema --truncate --indexes --constraints
```

`--truncate` は移行先テーブルを空にしてから投入します。実行前に Access 側の更新停止とバックアップを行ってください。

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

ビルド結果は `dist\外観検査記録照会.exe` です。

## 補足

- 検査員リストはアプリデザインに合わせた独自ドロップダウンで表示し、画面上は検査員IDではなく名前だけを表示します。
- 検査員別明細と検査員別集計の列順は Access 画面に合わせています。
- `production_lot_summary` / `production_lot_aggregate` view は使用しません。
- PostgreSQL 側の物理名は英語表記、画面と Excel 出力の表示列は日本語表記です。
