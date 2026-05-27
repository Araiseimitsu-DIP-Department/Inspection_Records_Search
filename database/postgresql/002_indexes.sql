CREATE INDEX IF NOT EXISTS idx_appearance_records_inspector_date_time
    ON appearance_records (inspector_id, inspection_date, inspection_time);

CREATE INDEX IF NOT EXISTS idx_appearance_records_lot
    ON appearance_records (production_lot_id);

CREATE INDEX IF NOT EXISTS idx_appearance_summary_inspector_date
    ON appearance_summary (inspector_id, inspection_date);

CREATE INDEX IF NOT EXISTS idx_appearance_summary_date_part
    ON appearance_summary (inspection_date, part_number);

CREATE INDEX IF NOT EXISTS idx_appearance_summary_lot
    ON appearance_summary (production_lot_id);

CREATE INDEX IF NOT EXISTS idx_appearance_summary_process
    ON appearance_summary (process_no);

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
