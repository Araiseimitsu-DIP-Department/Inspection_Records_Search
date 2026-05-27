SELECT 'appearance_records' AS target, COUNT(*) AS row_count FROM appearance_records
UNION ALL SELECT 'appearance_summary', COUNT(*) FROM appearance_summary
UNION ALL SELECT 'process_master', COUNT(*) FROM process_master
UNION ALL SELECT 'numeric_inspector_master', COUNT(*) FROM numeric_inspector_master
UNION ALL SELECT 'numeric_inspection_records', COUNT(*) FROM numeric_inspection_records
UNION ALL SELECT 'inspector_master', COUNT(*) FROM inspector_master
UNION ALL SELECT 'product_catalog', COUNT(*) FROM product_catalog;

SELECT 'appearance_records.id duplicate' AS check_name, COUNT(*) AS issue_count
FROM (
    SELECT id FROM appearance_records GROUP BY id HAVING COUNT(*) > 1
) s
UNION ALL
SELECT 'appearance_summary.id duplicate', COUNT(*)
FROM (
    SELECT id FROM appearance_summary GROUP BY id HAVING COUNT(*) > 1
) s
UNION ALL
SELECT 'numeric_inspection_records.id duplicate', COUNT(*)
FROM (
    SELECT id FROM numeric_inspection_records GROUP BY id HAVING COUNT(*) > 1
) s;

SELECT 'summary missing inspector' AS check_name, COUNT(*) AS issue_count
FROM appearance_summary s
LEFT JOIN inspector_master m ON s.inspector_id = m.inspector_id
WHERE m.inspector_id IS NULL
UNION ALL
SELECT 'numeric record missing inspector', COUNT(*)
FROM numeric_inspection_records r
LEFT JOIN numeric_inspector_master m ON r.inspector_id = m.inspector_id
WHERE m.inspector_id IS NULL
UNION ALL
SELECT 'summary missing lot', COUNT(*)
FROM appearance_summary s
LEFT JOIN product_catalog p ON s.production_lot_id = p.production_lot_id
WHERE s.production_lot_id IS NOT NULL AND p.production_lot_id IS NULL;

SELECT COUNT(*) AS app_main_detail_candidate_count
FROM appearance_summary s
LEFT JOIN inspector_master m ON s.inspector_id = m.inspector_id
LEFT JOIN numeric_inspection_records nr ON s.production_lot_id = nr.production_lot_id
LEFT JOIN numeric_inspector_master nm ON nr.inspector_id = nm.inspector_id;
