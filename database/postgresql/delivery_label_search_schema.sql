-- PostgreSQL schema for delivery_label_search_db.
-- Source: docs/delivery_label_search_db.

CREATE TABLE IF NOT EXISTS delivery_label_search (
    production_lot_id varchar(7),
    machine_no varchar(5),
    product_code varchar(30),
    product_name varchar(30),
    customer varchar(30),
    instruction_date timestamp,
    quantity integer
);

CREATE INDEX IF NOT EXISTS idx_delivery_label_search_lot_product
    ON delivery_label_search (production_lot_id, product_code);

CREATE INDEX IF NOT EXISTS idx_delivery_label_search_instruction_date
    ON delivery_label_search (instruction_date);
