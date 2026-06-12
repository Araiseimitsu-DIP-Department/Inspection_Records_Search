CREATE INDEX IF NOT EXISTS idx_app_records_inspector_date_time
    ON appearance_inspection_records (inspector_id, inspection_date, time_at);

CREATE INDEX IF NOT EXISTS idx_app_records_lot
    ON appearance_inspection_records (production_lot_id);

CREATE INDEX IF NOT EXISTS idx_app_records_product
    ON appearance_inspection_records (product_code);

CREATE INDEX IF NOT EXISTS idx_app_summaries_inspector_date
    ON appearance_inspection_summaries (inspector_id, inspection_date);

CREATE INDEX IF NOT EXISTS idx_app_summaries_date_product
    ON appearance_inspection_summaries (inspection_date, product_code);

CREATE INDEX IF NOT EXISTS idx_app_summaries_lot
    ON appearance_inspection_summaries (production_lot_id);

CREATE INDEX IF NOT EXISTS idx_app_summaries_process
    ON appearance_inspection_summaries (process_no);

CREATE INDEX IF NOT EXISTS idx_excel_product_slip_history_lot_product
    ON excel_product_slip_history (production_lot_id, product_code);

CREATE INDEX IF NOT EXISTS idx_defect_information_lot_product
    ON defect_information (production_lot_id, product_code);

CREATE INDEX IF NOT EXISTS idx_numeric_records_lot
    ON numeric_inspection_records (production_lot_id);

CREATE INDEX IF NOT EXISTS idx_numeric_records_inspector
    ON numeric_inspection_records (inspector_id);

CREATE INDEX IF NOT EXISTS idx_inspector_master_id
    ON inspector_master (inspector_id);

CREATE INDEX IF NOT EXISTS idx_numeric_inspector_master_id
    ON numeric_inspector_master (inspector_id);

CREATE INDEX IF NOT EXISTS idx_process_master_no
    ON process_master (process_no);
