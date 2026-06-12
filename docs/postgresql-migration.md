# Access -> PostgreSQL 移行手順書

## 目的

Access データを PostgreSQL へ移行し、アプリを `DB_BACKEND=postgres` で運用できるようにするための手順です。
PostgreSQL 側の物理名は英語表記に統一し、画面と Excel 出力では従来どおり日本語の列名を表示します。

## 対象データベース

| 区分 | フォルダ | PostgreSQL DB | 用途 |
|---|---|---|---|
| 外観検査 | `docs/appearance_inspection_db/` | `appearance_inspection_db` | 外観検査記録、集計、工程、検査員マスタ |
| 現品票検索 | `docs/delivery_label_search_db/` | `delivery_label_search_db` | ロットID集計の数量参照 |

接続例:

```env
DB_BACKEND=postgres
POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/appearance_inspection_db
DELIVERY_LABEL_POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/delivery_label_search_db
POSTGRES_SCHEMA=public
```

## 現在の方針

- Access のクエリは PostgreSQL view ではなく Python で再現します。
- `production_lot_summary` と `production_lot_aggregate` は使用しません。作成済みの場合は削除対象です。
- ロットID集計は `PostgresInspectionRepository.fetch_lot_aggregate()` で処理します。
- 作業時間は `appearance_inspection_summaries.work_time` をロット、工程、品番、品名単位で合計します。
- 数量は `delivery_label_search_db.delivery_label_search.quantity` を生産ロットIDで参照します。見つからない場合だけ外観検査集計側の数量を補助値として使用します。

## テーブルマッピング

### appearance_inspection_db

| Access テーブル | PostgreSQL テーブル | 用途 |
|---|---|---|
| `t_製品伝票履歴` | `excel_product_slip_history` | ロット、品番、現品票の履歴 |
| `t_チェックシートリスト` | `check_sheet_list` | チェックシート情報 |
| `t_不良内容` | `defect_information` | 不良内容マスタ |
| `t_外観検査記録` | `appearance_inspection_records` | 検査員別照会の明細 |
| `t_外観検査記録アーカイブ` | `appearance_inspection_record_archives` | 外観検査記録アーカイブ |
| `t_外観検査集計` | `appearance_inspection_summaries` | 検査員別集計、ロットID集計の作業時間元 |
| `t_外観検査集計アーカイブ` | `appearance_inspection_summary_archives` | 外観検査集計アーカイブ |
| `t_工程マスタ` | `process_master` | 工程凡例 |
| `t_数値検査員マスタ` | `numeric_inspector_master` | 数値検査員名 |
| `t_数値検査記録` | `numeric_inspection_records` | 数値検査情報 |
| `t_検査中` | `inspection_in_progress` | 検査中データ |
| `t_検査員マスタ` | `inspector_master` | 検査員候補、検査員名 |
| `t_検査員マスタ_個人データ用` | `inspection_person_master` | 個人データ用検査員マスタ |

### delivery_label_search_db

| Access テーブル | PostgreSQL テーブル | 用途 |
|---|---|---|
| `T_現品票検索用` | `delivery_label_search` | 生産ロットIDごとの数量参照 |

## 主なカラム名

| Access カラム | PostgreSQL カラム |
|---|---|
| `生産ロットID` | `production_lot_id` |
| `工程NO` | `process_no` |
| `品番` | `product_code` |
| `品名` | `product_name` |
| `客先` | `customer` |
| `数量` | `quantity` |
| `作業時間` | `work_time` |
| `日付` | `inspection_date` |
| `時刻` | `inspection_time` |
| `検査員ID` | `inspector_id` |
| `検査員名` | `inspector_name` |
| `集計除外フラグ` | `aggregation_exclusion_flag` |
| `表示フラグ` | `display_flag` |
| `表示位置` | `display_position` |
| `ふりがな` | `furigana` |
| `日付時刻` | `inspected_at` |

## PostgreSQL関連ファイル

| ファイル | 役割 |
|---|---|
| `database/postgresql/001_schema.sql` | `appearance_inspection_db` のテーブル作成 |
| `database/postgresql/002_indexes.sql` | `appearance_inspection_db` の検索用インデックス |
| `database/postgresql/003_constraints.sql` | `appearance_inspection_db` の制約 |
| `database/postgresql/020_validation.sql` | `appearance_inspection_db` の検証SQL |
| `database/postgresql/delivery_label_search_schema.sql` | `delivery_label_search_db` のテーブルとインデックス |
| `database/postgresql/migration_notes.md` | 移行メモ |
| `scripts/migrate_access_to_postgres.py` | Access から PostgreSQL への投入スクリプト |

## アプリ側の実装

```text
src/inspection_records_search/config.py
src/inspection_records_search/infrastructure/repository_factory.py
src/inspection_records_search/infrastructure/postgres_repository.py
src/inspection_records_search/web/index.html
```

PostgreSQL repository は英語列名を SELECT し、画面互換のため日本語 alias を付けて `TableData = tuple[list[str], list[tuple]]` を返します。

## 移行手順

### 1. 事前停止

Access アプリ利用者へ停止時間を連絡し、移行中は Access 側を更新しない状態にします。

### 2. バックアップ

Access ファイルと PostgreSQL の既存データベースをバックアップします。

### 3. dry-run

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --dry-run
```

### 4. 検証投入 / 完全再投入

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --apply-schema --truncate --indexes --constraints
```

このスクリプトは `appearance_inspection_db` のスキーマ適用、既存データ削除、Access データ投入、インデックス、制約適用を行います。
`--truncate` は移行先テーブルを空にするため、本番実行前に必ずバックアップしてください。

`delivery_label_search_db` は別DBのため、`database/postgresql/delivery_label_search_schema.sql` を適用し、現品票検索データを同DBへ投入してください。

### 5. 検証

`database/postgresql/020_validation.sql` を実行し、次を確認します。

- 13テーブルの件数
- `id` の重複
- 検査員IDの参照欠損
- 数値検査員IDの参照欠損
- 外観検査集計のロットID参照状況
- Access 画面と PostgreSQL アプリ画面の件数、数量、作業時間

特にロットID集計では、Access と同じ品番で次を比較します。

- 表示件数
- 生産ロットID
- 工程NO
- 数量
- 作業時間

### 6. アプリ確認

`.env` を `DB_BACKEND=postgres` にして起動します。

```powershell
.\.venv\Scripts\python.exe main.py
```

確認する操作:

- アプリ起動
- 検査員候補の表示
- 検査員別照会
- 検査員別明細と検査員別集計の列順
- ロットID集計
- 数量のカンマ区切り表示
- Excel 出力

## 切り戻し

問題があれば `.env` を Access に戻します。

```env
DB_BACKEND=access
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\外観検査記録照会.accdb
POSTGRES_SCHEMA=public
```

## 本番移行時の注意

PostgreSQL へ投入した後も Access 側が更新され続けると、Access 画面と PostgreSQL アプリ画面の件数や数量に差異が出ます。
本番切替時は Access 側の更新停止後に最新データを再投入するか、差分同期を実行してください。
