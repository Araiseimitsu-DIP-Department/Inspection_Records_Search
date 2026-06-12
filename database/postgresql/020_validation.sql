SELECT 'excel_product_slip_history' AS target, COUNT(*) AS row_count FROM excel_product_slip_history
UNION ALL SELECT 'check_sheet_list', COUNT(*) FROM check_sheet_list
UNION ALL SELECT 'defect_information', COUNT(*) FROM defect_information
UNION ALL SELECT 'appearance_inspection_records', COUNT(*) FROM appearance_inspection_records
UNION ALL SELECT 'appearance_inspection_record_archives', COUNT(*) FROM appearance_inspection_record_archives
UNION ALL SELECT 'appearance_inspection_summaries', COUNT(*) FROM appearance_inspection_summaries
UNION ALL SELECT 'appearance_inspection_summary_archives', COUNT(*) FROM appearance_inspection_summary_archives
UNION ALL SELECT 'process_master', COUNT(*) FROM process_master
UNION ALL SELECT 'numeric_inspector_master', COUNT(*) FROM numeric_inspector_master
UNION ALL SELECT 'numeric_inspection_records', COUNT(*) FROM numeric_inspection_records
UNION ALL SELECT 'inspection_in_progress', COUNT(*) FROM inspection_in_progress
UNION ALL SELECT 'inspector_master', COUNT(*) FROM inspector_master
UNION ALL SELECT 'inspection_person_master', COUNT(*) FROM inspection_person_master;

SELECT 'defect_information.id duplicate' AS check_name, COUNT(*) AS issue_count
FROM (
    SELECT id FROM defect_information GROUP BY id HAVING COUNT(*) > 1
) s
UNION ALL
SELECT 'appearance_inspection_records.id duplicate', COUNT(*)
FROM (
    SELECT id FROM appearance_inspection_records GROUP BY id HAVING COUNT(*) > 1
) s
UNION ALL
SELECT 'appearance_inspection_summaries.id duplicate', COUNT(*)
FROM (
    SELECT id FROM appearance_inspection_summaries GROUP BY id HAVING COUNT(*) > 1
) s
UNION ALL
SELECT 'numeric_inspection_records.id duplicate', COUNT(*)
FROM (
    SELECT id FROM numeric_inspection_records GROUP BY id HAVING COUNT(*) > 1
) s;

SELECT 'summary missing inspector' AS check_name, COUNT(*) AS issue_count
FROM appearance_inspection_summaries s
LEFT JOIN inspector_master m ON s.inspector_id = m.inspector_id
WHERE m.inspector_id IS NULL
UNION ALL
SELECT 'numeric record missing inspector', COUNT(*)
FROM numeric_inspection_records r
LEFT JOIN numeric_inspector_master m ON r.inspector_id = m.inspector_id
WHERE r.inspector_id IS NOT NULL AND m.inspector_id IS NULL
UNION ALL
SELECT 'summary missing lot in excel history', COUNT(*)
FROM appearance_inspection_summaries s
LEFT JOIN excel_product_slip_history p ON s.production_lot_id = p.production_lot_id
WHERE s.production_lot_id IS NOT NULL AND p.production_lot_id IS NULL;

SELECT COUNT(*) AS app_main_detail_candidate_count
FROM appearance_inspection_summaries s
LEFT JOIN inspector_master m ON s.inspector_id = m.inspector_id
LEFT JOIN numeric_inspection_records nr ON s.production_lot_id = nr.production_lot_id
LEFT JOIN numeric_inspector_master nm ON nr.inspector_id = nm.inspector_id;
