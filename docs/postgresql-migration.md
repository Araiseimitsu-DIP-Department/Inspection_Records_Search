# Access -> PostgreSQL 移行手順書

## 目的

既存の Access データベース `外観検査記録照会.accdb` を PostgreSQL へ移行するための手順書です。

PostgreSQL 側の物理名は英語表記に統一します。Access 側の元テーブル・元カラムは日本語名のまま読み取り、移行スクリプトで PostgreSQL の英語名へマッピングします。アプリ画面と Excel 出力の表示列は従来どおり日本語名です。

## 現時点の状態

- `docs/` 配下の Access メタデータ、DDL 草案、VBA、フォーム抽出を確認済み
- PostgreSQL repository は英語物理名参照へ移行済み
- 移行 SQL と Access -> PostgreSQL 投入スクリプトは英語物理名対応済み
- PostgreSQL 接続テスト、検証投入、インデックス、制約、検証まで完了
- `DB_BACKEND=postgres` で検索と Excel 出力の実画面確認済み
- 前回作成した日本語物理名の PostgreSQL テーブル / view は削除済み

## 移行元

```text
\\192.168.1.200\共有\品質保証課\外観検査記録\外観検査記録照会.accdb
```

## 移行先

```env
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\外観検査記録照会.accdb
DB_BACKEND=postgres
POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/inspection_records_search
POSTGRES_SCHEMA=public
EXPORT_DIR=
```

## 物理名マッピング

| Access テーブル | PostgreSQL テーブル | 用途 |
|---|---|---|
| `t_外観検査記録` | `appearance_records` | 検査員別照会の明細 |
| `t_外観検査集計` | `appearance_summary` | メイン検索、検査員別照会の集計、ロット集計元 |
| `t_工程マスタ` | `process_master` | 工程凡例 |
| `t_数値検査員マスタ` | `numeric_inspector_master` | 数値検査員名 |
| `t_数値検査記録` | `numeric_inspection_records` | 生産ロットID経由の数値検査情報 |
| `t_検査員マスタ` | `inspector_master` | 検査員候補、検査員名 |
| `t_現品票検索用` | `product_catalog` | ロット・品番・指示日情報 |
| `Q_生産ロットまとめ` | `production_lot_summary` | ロット集計 view |
| `Q_生産ロット集計` | `production_lot_aggregate` | アプリ用ロット集計 view |

| Access カラム | PostgreSQL カラム | 対象 |
|---|---|---|
| `ID` | `id` | `appearance_records`, `appearance_summary`, `numeric_inspection_records` |
| `検査員ID` | `inspector_id` | 各検査員系テーブル |
| `検査員名` | `inspector_name` | `inspector_master`, `numeric_inspector_master` |
| `生産ロットID` | `production_lot_id` | ロット参照系 |
| `工程NO` | `process_no` | 外観検査・工程・ロット集計 |
| `工程名` | `process_name` | `process_master`, `numeric_inspection_records` |
| `日付` | `inspection_date` | `appearance_records`, `appearance_summary` |
| `時刻` | `inspection_time` | `appearance_records` |
| `品番` | `part_number` | 外観検査・現品票 |
| `品名` | `part_name` | 外観検査・現品票 |
| `客先` | `customer_name` | 外観検査・現品票 |
| `数量` | `quantity` | 外観検査・現品票・view |
| `作業時間` | `work_minutes` | `appearance_summary` |
| `作業時間の合計` | `total_work_minutes` | `production_lot_summary`, `production_lot_aggregate` |
| `更新フラグ` | `updated_flag` | `appearance_records` |
| `集計除外フラグ` | `excluded_from_summary` | `appearance_records`, `appearance_summary` |
| `日付時刻` | `recorded_at` | `numeric_inspection_records` |
| `号機` | `machine_no` | `numeric_inspection_records`, `product_catalog` |
| `区別` | `category` | `numeric_inspector_master` |
| `表示フラグ` | `visible` | `numeric_inspector_master` |
| `表示位置` | `display_order` | `inspector_master` |
| `チーム` | `team` | `inspector_master` |
| `ふりがな` | `kana` | `inspector_master` |
| `指示日` | `instruction_date` | `product_catalog` |

## PostgreSQL ファイル

| ファイル | 役割 |
|---|---|
| `database/postgresql/001_schema.sql` | 英語物理名のテーブルと view 作成 |
| `database/postgresql/002_indexes.sql` | 検索用インデックス |
| `database/postgresql/003_constraints.sql` | PK / UNIQUE / CHECK 制約 |
| `database/postgresql/020_validation.sql` | 件数・重複・参照欠損検証 |
| `database/postgresql/migration_notes.md` | 実行結果メモ |
| `scripts/migrate_access_to_postgres.py` | Access 日本語物理名から PostgreSQL 英語物理名への投入スクリプト |

## アプリ側の実装

PostgreSQL 側は次の実装が英語物理名を参照します。

```text
src/inspection_records_search/infrastructure/postgres_repository.py
src/inspection_records_search/infrastructure/repository_factory.py
src/inspection_records_search/config.py
```

PostgreSQL repository は英語列名を SELECT し、画面互換のため日本語 alias を付けて `TableData = tuple[list[str], list[tuple]]` を返します。

## 本番移行手順

### 1. 事前停止

Access アプリ利用者へ停止時間を連絡し、移行中は Access 側を更新しない状態にします。

### 2. バックアップ

Access ファイルと PostgreSQL の既存DBをバックアップします。

### 3. dry-run

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --dry-run
```

### 4. 検証投入 / 完全移行時の投入

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --apply-schema --truncate --indexes --constraints
```

このスクリプトは次を行います。

- Access 7テーブルを読み取り
- PostgreSQL 英語物理名へ変換して投入
- `id` identity sequence を調整
- `numeric_inspection_records` 側にだけ存在する旧検査員IDを `numeric_inspector_master` へ `未登録` / `補正` / `visible=false` として補完
- schema / indexes / constraints を適用

2026-05-27 の英語物理名検証投入結果:

```text
appearance_records: 66,513 rows
appearance_summary: 49,701 rows
process_master: 10 rows
numeric_inspector_master: 21 rows
numeric_inspection_records: 24,943 rows
inspector_master: 76 rows
product_catalog: 168,837 rows
```

### 5. 検証

PostgreSQL 接続後、`database/postgresql/020_validation.sql` を実行します。

確認項目:

- 7テーブルの件数
- `id` の重複
- `appearance_summary.inspector_id -> inspector_master.inspector_id` の参照欠損
- `numeric_inspection_records.inspector_id -> numeric_inspector_master.inspector_id` の参照欠損
- `appearance_summary.production_lot_id -> product_catalog.production_lot_id` の参照欠損
- アプリのメイン検索 JOIN 候補件数

### 6. アプリ確認

`.env` を `DB_BACKEND=postgres` にして `main.py` を起動します。

```powershell
.\.venv\Scripts\python.exe main.py
```

確認する操作:

- アプリ起動
- 検査員候補の表示
- 検査員別照会
- メイン検索の日付範囲検索
- 品番検索
- 生産ロットID別集計
- 工程条件検索
- Excel 出力

## 切り戻し

問題があれば `.env` を Access に戻します。

```env
DB_BACKEND=access
ACCESS_DB_PATH=\\192.168.1.200\共有\品質保証課\外観検査記録\外観検査記録照会.accdb
POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/inspection_records_search
POSTGRES_SCHEMA=public
```

## 完全移行前の状態

現時点では PostgreSQL への検証投入とアプリ確認まで完了しています。完全移行はまだ実施していません。

完全移行時は Access の更新を止め、バックアップ後に `--apply-schema --truncate --indexes --constraints` で最新データを一括再投入します。

## 本番移行を依頼するときの指示例

```text
PostgreSQL本番移行を実行してください。
手順は docs/postgresql-migration.md と database/postgresql/migration_notes.md に従ってください。
実行前に dry-run を行い、件数を確認してから --apply-schema --truncate --indexes --constraints で本投入してください。
投入後、020_validation.sql を実行し、結果を migration_notes.md に記録してください。
アプリ確認は DB_BACKEND=postgres に切り替えて main.py から実施してください。
```
