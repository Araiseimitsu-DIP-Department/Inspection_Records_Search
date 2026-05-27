# PostgreSQL migration notes

## Status

- Prepared: 2026-05-27
- Dry-run: completed
- PostgreSQL connection test: completed
- English schema/import/index/constraint: completed
- Validation: completed
- App repository smoke test: completed

## Expected Access row counts

These counts come from the latest English-name production import on 2026-05-27.

```text
appearance_records: 66,513
appearance_summary: 49,701
process_master: 10
numeric_inspector_master: 21
numeric_inspection_records: 24,943
inspector_master: 76
product_catalog: 168,837
total: 310,101
```

## Execution log

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --dry-run
```

Result:

```text
Access: \\192.168.1.200\共有\品質保証課\外観検査記録\外観検査記録照会.accdb
t_外観検査記録: 66,503 rows
t_外観検査集計: 49,693 rows
t_工程マスタ: 10 rows
t_数値検査員マスタ: 14 rows
t_数値検査記録: 24,943 rows
t_検査員マスタ: 76 rows
t_現品票検索用: 168,837 rows
```

## Import

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --apply-schema --truncate --indexes --constraints
```

Result:

```text
Access source:
t_外観検査記録: 66,513 rows
t_外観検査集計: 49,701 rows
t_工程マスタ: 10 rows
t_数値検査員マスタ: 14 rows
t_数値検査記録: 24,943 rows
t_検査員マスタ: 76 rows
t_現品票検索用: 168,837 rows

PostgreSQL destination:
imported appearance_records: 66,513 rows
imported appearance_summary: 49,701 rows
imported process_master: 10 rows
imported numeric_inspector_master: 14 rows
imported numeric_inspection_records: 24,943 rows
imported inspector_master: 76 rows
imported product_catalog: 168,837 rows
inserted numeric_inspector_master placeholders: 7 rows
```

The previous Japanese-name PostgreSQL objects were removed after the English
schema was verified.

## Validation

```text
duplicate appearance_records.id: 0
duplicate appearance_summary.id: 0
duplicate numeric_inspection_records.id: 0
summary missing inspector: 0
numeric record missing inspector: 26
summary missing lot: 0
```

The 26 missing numeric inspector references were repaired without changing
the inspection records. Seven non-visible placeholder rows were added to
`numeric_inspector_master`.

```text
inserted numeric_inspector_master placeholders: 7
placeholder IDs: 00, 10, 2, 3, 30, 31, 71
numeric record missing inspector after repair: 0
```

## Repository smoke test

```text
repository: PostgresInspectionRepository
inspectors: 76
main_detail_2025-01-06: 115
lot_aggregate: 27048
```

## Connection test

The app-style `.env` keys were confirmed:

```text
DB_BACKEND=postgres
POSTGRES_CONNECTION_URL=(set)
POSTGRES_SCHEMA=public
```

Result:

```text
database: inspection_records_search
schema: public
server: 192.168.1.120:5432
connection: OK
objects checked: t_外観検査記録, t_外観検査集計, Q_生産ロット集計
objects found before import: none
objects checked after English import: appearance_records, appearance_summary, production_lot_aggregate
objects found after English import: all expected objects
```
