# 外観検査記録照会 アーキテクチャ

## 1. アーキテクチャ説明

このアプリは、Access 依存を UI から切り離し、将来 PostgreSQL に差し替えやすい最小構成で設計します。

- `presentation`: PySide6 の画面、入力、一覧表示
- `application`: ユースケース。画面から来た条件を受けて処理をまとめる
- `domain`: 業務概念、条件、値オブジェクト
- `infrastructure`: Access / ODBC の実装
- `shared`: 例外、ログ、共通メッセージ

画面は repository を直接知らず、`InspectionService` を通じてユースケースを呼びます。
`InspectionService` の内部で `AccessInspectionRepository` を使うため、後で `PostgresInspectionRepository` に差し替えても UI は変更しません。

## 2. フォルダ構成

```text
src/inspection_records_search/
  app.py
  config.py
  shared/
    errors.py
  domain/
    models.py
    repositories.py
  application/
    inspection_use_case.py
  infrastructure/
    access_gateway.py
  services/
    inspection_service.py   # 互換ラッパー
  ui/
    main_window.py
    ...
```

## 3. ドメインモデル

`domain/models.py` に、業務概念として使う型を置きます。

```python
@dataclass(frozen=True, slots=True)
class DateRange:
    start: date
    end: date

@dataclass(frozen=True, slots=True)
class PersonalInquiryCriteria:
    inspector_id: str
    date_range: DateRange

@dataclass(frozen=True, slots=True)
class LotAggregateCriteria:
    part_number: str | None = None
    process_value: str | None = None
```

ポイント:

- DB の列名は持たない
- `検査員ID` ではなく `inspector_id`
- `工程NO` ではなく `process_value`

## 4. Repository Interface

`domain/repositories.py` に repository 契約を置きます。

```python
class InspectionRepository(Protocol):
    @property
    def db_path(self) -> str: ...

    def fetch_inspectors(self) -> TableData: ...
    def fetch_personal_records(self, inspector_id, date_from, date_to) -> TableData: ...
    def fetch_personal_summary(self, inspector_id, date_from, date_to) -> TableData: ...
    def fetch_main_detail(self, date_from, date_to, part_number) -> TableData: ...
    def fetch_koutei_distinct_values(self) -> list[str]: ...
    def fetch_lot_aggregate(self, part_number, process_value) -> TableData: ...
```

`TableData` は当面 `tuple[list[str], list[tuple]]` を使っています。
これは既存の一覧 UI と Excel 出力への影響を最小化するためです。

## 5. Access 実装例

`infrastructure/access_gateway.py` に Access 実装を閉じ込めます。

```python
class AccessInspectionRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    @property
    def db_path(self) -> str:
        return self._db_path

    def fetch_inspectors(self) -> TableData:
        sql = (
            "SELECT 検査員ID, 検査員名 FROM t_検査員マスタ "
            "ORDER BY 検査員ID"
        )
        return execute_query(self._db_path, sql)
```

SQL、ODBC 接続、Access 特有の照合はここに集約します。

## 6. ユースケース例

`application/inspection_use_case.py` は業務処理の入口です。

```python
class InspectionUseCase:
    def __init__(self, repository: InspectionRepository) -> None:
        self._repository = repository

    def fetch_main_detail(self, date_from, date_to, part_number):
        DateRange(date_from, date_to).validate()
        return self._repository.fetch_main_detail(date_from, date_to, part_number)
```

ここでは次を担当します。

- 日付範囲の妥当性確認
- repository 呼び出しの仲介
- 将来の追加ルールの置き場

## 7. UI 呼び出し例

`ui/main_window.py` では `InspectionService` をそのまま使います。

```python
self._svc = InspectionService(db_path)

def task():
    return self._svc.fetch_main_detail(d0, d1, hinban)
```

画面は SQL を知らず、表示・入力・確認ダイアログだけを持ちます。

## 8. エラー処理設計

`shared/errors.py` で例外を定義し、画面表示用文言を分離します。

```python
class DatabaseUnavailableError(DatabaseError): ...
class DataConversionError(DatabaseError): ...
class DataIntegrityError(DatabaseError): ...
```

方針:

- `infrastructure` で `pyodbc.Error` を業務向け例外へ変換
- `ui` では `describe_exception()` で短いメッセージを表示
- 詳細ログは `logging.exception()` で残す

対象:

- DB 接続失敗
- NAS 未接続
- ODBC エラー
- データ不整合
- 型変換エラー

## 9. PostgreSQL 移行時の差し替えポイント

差し替え対象は `infrastructure` の repository だけです。

- `AccessInspectionRepository` を `PostgresInspectionRepository` に置換
- 接続文字列を `psycopg` / `SQLAlchemy` などに変更
- Access 固有関数 `Nz`、`Len`、`Trim`、`LEFT JOIN` 構文を PostgreSQL 用 SQL に調整
- `COUNTER` 相当は `BIGSERIAL` / `IDENTITY` に置換
- `工程NO` のコード・名称の揺れは repository 内で正規化

UI、application、domain は原則そのまま維持できます。

## 付記

今の実装は「まず動く最小構成」を優先しています。
次の拡張候補は以下です。

- 画面ごとの query DTO を導入する
- 一覧表示用の row モデルを domain 化する
- Postgres 用 repository を追加する
- Access / Postgres を設定で切り替える

## 追記

現在は次の切替点を実装済みです。

- `DATABASE_BACKEND`
- `POSTGRES_DSN`
- `EXPORT_DIR`
- `infrastructure/repository_factory.py`
- `services/inspection_service.py`

これにより、UI は repository の実装差を知らず、将来は Access から PostgreSQL に移行しやすい状態になっています。
