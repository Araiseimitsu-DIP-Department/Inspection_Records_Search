# Access → PostgreSQL 移行対応表

## 1. 移行概要

- 対象Access DB：\\192.168.1.200\共有\QRシステム\Access\現品票検索DB.accdb
- 移行先PostgreSQL DB：delivery_label_search_db
- 接続情報：
  - `.env` の DATABASE_URL を参照
- 移行日：2026-06-12 11:59:19
- 作成者：Codex
- 備考：現品票検索用の1テーブルを忠実に移行。日本語名はPostgreSQL用に英語のスネークケースへ変換し、元名はコメントと本対応表で追跡可能。

## 2. 移行対象テーブル一覧

| No | Accessテーブル名 | PostgreSQLテーブル名 | 種別 | Access件数 | PostgreSQL件数 | 備考 |
|---:|---|---|---|---:|---:|---|
| 1 | t_現品票検索用 | delivery_label_search | TABLE | 169836 | 169836 | 成功 |

## 3. テーブル別カラム対応表

### Accessテーブル名：t_現品票検索用
### PostgreSQLテーブル名：delivery_label_search

| No | Accessカラム名 | Access型 | PostgreSQLカラム名 | PostgreSQL型 | NULL許可 | 備考 |
|---:|---|---|---|---|---|---|
| 1 | 生産ロットID | VARCHAR | production_lot_id | VARCHAR(7) | 可 |  |
| 2 | 号機 | VARCHAR | machine_no | VARCHAR(5) | 可 |  |
| 3 | 品番 | VARCHAR | product_code | VARCHAR(30) | 可 |  |
| 4 | 品名 | VARCHAR | product_name | VARCHAR(30) | 可 |  |
| 5 | 客先 | VARCHAR | customer | VARCHAR(30) | 可 |  |
| 6 | 指示日 | DATETIME | instruction_date | TIMESTAMP | 可 | Accessの日付をtimestampで保持 |
| 7 | 数量 | INTEGER | quantity | INTEGER | 可 | NULLが存在するためNULL許可のINTEGERで保持 |

## 4. 主キー・インデックス情報

| Accessテーブル名 | PostgreSQLテーブル名 | 主キー | インデックス | 備考 |
|---|---|---|---|---|
| t_現品票検索用 | delivery_label_search | 検出なし | 検出なし | FKは未検出 |

## 5. 型変換ルール

| Access型 | PostgreSQL型 | 備考 |
|---|---|---|
| VARCHAR | varchar(n) | Accessのサイズを維持 |
| INTEGER | integer | 整数。NULLはNULLのまま保持 |
| DATETIME | timestamp | Accessの日付を保持 |

## 6. アプリ接続時の参照情報

### 接続先

```text
.env の DATABASE_URL を使用
```

### 主に参照するテーブル

| 用途 | PostgreSQLテーブル名 | 主なキー | 備考 |
| -- | --------------- | ---- | -- |
| 現品票検索 | delivery_label_search | production_lot_id, product_code | 元 t_現品票検索用 |

### 主要カラム

| 用途 | PostgreSQLテーブル名 | PostgreSQLカラム名 | 元Accessカラム名 | 備考 |
| -- | --------------- | -------------- | ----------- | -- |
| 生産ロット | delivery_label_search | production_lot_id | 生産ロットID | Accessの値をそのまま保持 |
| 号機 | delivery_label_search | machine_no | 号機 | Accessの値をそのまま保持 |
| 品番 | delivery_label_search | product_code | 品番 | Accessの値をそのまま保持 |
| 品名 | delivery_label_search | product_name | 品名 | Accessの値をそのまま保持 |
| 客先 | delivery_label_search | customer | 客先 | Accessの値をそのまま保持 |
| 指示日 | delivery_label_search | instruction_date | 指示日 | Accessの値をそのまま保持 |
| 数量 | delivery_label_search | quantity | 数量 | Accessの値をそのまま保持 |

## 7. 注意事項・要確認事項

- AccessのFKメタデータはODBCドライバが返さなかったため、外部キー制約は作成していません。
- 主キーはメタデータ上は検出なしです。
- `数量` はAccess側にNULLが2件あるため、PostgreSQLでもNULL許可のintegerとして保持しています。
- `.env` の `ACCESS_DB_PATH` が実ファイルを指していない場合は、メタJSONの `database_path` を使用しています。
- メタ抽出警告：FK 取得スキップ: t_現品票検索用 — ('IM001', '[IM001] [Microsoft][ODBC Driver Manager] ドライバーはこの関数をサポートしていません。 (0) (SQLForeignKeys)')
- メタ抽出警告：VBA 抽出失敗: (-2147352567, '例外が発生しました。', (0, None, '指定した式に、Visible プロパティに対する正しくない参照が含まれます。', 'dao360.chm', 2015567, -2146825833), None)
