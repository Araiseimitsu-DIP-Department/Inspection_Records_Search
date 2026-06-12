DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_defect_information') THEN
        ALTER TABLE defect_information ADD CONSTRAINT pk_defect_information PRIMARY KEY (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_appearance_inspection_records') THEN
        ALTER TABLE appearance_inspection_records ADD CONSTRAINT pk_appearance_inspection_records PRIMARY KEY (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_appearance_inspection_record_archives') THEN
        ALTER TABLE appearance_inspection_record_archives ADD CONSTRAINT pk_appearance_inspection_record_archives PRIMARY KEY (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_appearance_inspection_summaries') THEN
        ALTER TABLE appearance_inspection_summaries ADD CONSTRAINT pk_appearance_inspection_summaries PRIMARY KEY (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_appearance_inspection_summary_archives') THEN
        ALTER TABLE appearance_inspection_summary_archives ADD CONSTRAINT pk_appearance_inspection_summary_archives PRIMARY KEY (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_numeric_inspection_records') THEN
        ALTER TABLE numeric_inspection_records ADD CONSTRAINT pk_numeric_inspection_records PRIMARY KEY (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'pk_inspection_person_master') THEN
        ALTER TABLE inspection_person_master ADD CONSTRAINT pk_inspection_person_master PRIMARY KEY (id);
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
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_app_records_quantity_nonnegative') THEN
        ALTER TABLE appearance_inspection_records
            ADD CONSTRAINT ck_app_records_quantity_nonnegative
            CHECK (quantity IS NULL OR quantity >= 0) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_app_summaries_quantity_nonnegative') THEN
        ALTER TABLE appearance_inspection_summaries
            ADD CONSTRAINT ck_app_summaries_quantity_nonnegative
            CHECK (quantity IS NULL OR quantity >= 0) NOT VALID;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'ck_app_summaries_work_time_nonnegative') THEN
        ALTER TABLE appearance_inspection_summaries
            ADD CONSTRAINT ck_app_summaries_work_time_nonnegative
            CHECK (work_time IS NULL OR work_time >= 0) NOT VALID;
    END IF;
END $$;
