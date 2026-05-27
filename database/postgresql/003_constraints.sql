DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_appearance_records') THEN
        ALTER TABLE appearance_records ADD CONSTRAINT pk_appearance_records PRIMARY KEY (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_appearance_summary') THEN
        ALTER TABLE appearance_summary ADD CONSTRAINT pk_appearance_summary PRIMARY KEY (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_numeric_inspection_records') THEN
        ALTER TABLE numeric_inspection_records ADD CONSTRAINT pk_numeric_inspection_records PRIMARY KEY (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_process_master_no') THEN
        ALTER TABLE process_master ADD CONSTRAINT uq_process_master_no UNIQUE (process_no);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_inspector_master_id') THEN
        ALTER TABLE inspector_master ADD CONSTRAINT uq_inspector_master_id UNIQUE (inspector_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_numeric_inspector_master_id') THEN
        ALTER TABLE numeric_inspector_master ADD CONSTRAINT uq_numeric_inspector_master_id UNIQUE (inspector_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_appearance_records_quantity_nonnegative') THEN
        ALTER TABLE appearance_records
            ADD CONSTRAINT ck_appearance_records_quantity_nonnegative
            CHECK (quantity IS NULL OR quantity >= 0) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_appearance_summary_quantity_nonnegative') THEN
        ALTER TABLE appearance_summary
            ADD CONSTRAINT ck_appearance_summary_quantity_nonnegative
            CHECK (quantity IS NULL OR quantity >= 0) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_appearance_summary_work_minutes_nonnegative') THEN
        ALTER TABLE appearance_summary
            ADD CONSTRAINT ck_appearance_summary_work_minutes_nonnegative
            CHECK (work_minutes IS NULL OR work_minutes >= 0) NOT VALID;
    END IF;
END $$;
