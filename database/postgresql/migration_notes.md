# PostgreSQL migration notes

## Status

- Updated: 2026-06-12
- Current app backend: PostgreSQL supported through `DB_BACKEND=postgres`
- Primary DB: `appearance_inspection_db`
- Delivery label DB: `delivery_label_db`
- Lot aggregation: calculated in Python, not PostgreSQL views

## Current PostgreSQL objects

`appearance_inspection_db` uses these application tables:

```text
excel_product_slip_history
check_sheet_list
defect_information
appearance_inspection_records
appearance_inspection_record_archives
appearance_inspection_summaries
appearance_inspection_summary_archives
process_master
numeric_inspector_master
numeric_inspection_records
inspection_in_progress
inspector_master
inspection_person_master
```

`delivery_label_db` uses:

```text
delivery_label_history
```

The old lot aggregation views are obsolete and should not exist:

```text
production_lot_summary
production_lot_aggregate
```

## App behavior notes

- `PostgresInspectionRepository.fetch_lot_aggregate()` reproduces the Access lot aggregation in Python.
- Work time is summed from `appearance_inspection_summaries.work_time`.
- Quantity is looked up from `delivery_label_db.delivery_label_history.quantity` by `production_lot_id`.
- Inspector dropdown labels show names only, while the app still resolves the underlying inspector ID.
- Personal detail and personal summary column order follows the Access screens.
- Quantity display in the web UI is comma-separated.

## Environment

```env
DB_BACKEND=postgres
POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/appearance_inspection_db
DELIVERY_LABEL_POSTGRES_CONNECTION_URL=postgresql://postgres:password@192.168.1.120:5432/delivery_label_db
POSTGRES_SCHEMA=public
```

Compatibility variables are still accepted:

```text
DATABASE_BACKEND
POSTGRES_DSN
DATABASE_URL
DELIVERY_LABEL_DATABASE_URL
```

## Migration command

Dry-run:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --dry-run
```

Full reload for `appearance_inspection_db`:

```powershell
.\.venv\Scripts\python.exe scripts\migrate_access_to_postgres.py --apply-schema --truncate --indexes --constraints
```

`--truncate` clears target tables before import. Run it only after stopping Access updates and taking backups.

`delivery_label_search_db` is retired. Use the existing `delivery_label_db.delivery_label_history` table instead.

## Validation checklist

- `database/postgresql/020_validation.sql` returns expected counts and no unexpected duplicates.
- `production_lot_summary` and `production_lot_aggregate` are absent.
- Lot aggregation for `06131-05511K` matches Access quantities for sampled lots such as `P153636`, `P153687`, and `P154186`.
- Inspector-specific detail and summary counts match Access for the same inspector and date range.
- Build output starts with `DB_BACKEND=postgres` and can search/export without database errors.

## Known operational note

If Access continues to receive new rows after PostgreSQL import, Access and PostgreSQL search results will differ.
Before production cutover, stop Access updates and reload the latest data, or run a controlled incremental sync.
