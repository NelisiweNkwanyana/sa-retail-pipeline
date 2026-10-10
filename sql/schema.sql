-- ============================================================
-- SA Retail Pipeline — Database Schema
-- Three layers: raw -> staging -> marts
-- ============================================================

DROP SCHEMA IF EXISTS raw CASCADE;
DROP SCHEMA IF EXISTS staging CASCADE;
DROP SCHEMA IF EXISTS marts CASCADE;

CREATE SCHEMA raw;
CREATE SCHEMA staging;
CREATE SCHEMA marts;

-- ============================================================
-- RAW LAYER
-- ============================================================
CREATE TABLE raw.sales_raw (
    transaction_id   TEXT,
    sale_date        TEXT,
    store_id         TEXT,
    store_name       TEXT,
    product_id       TEXT,
    product_name     TEXT,
    category         TEXT,
    quantity         TEXT,
    unit_price       TEXT,
    total_amount     TEXT,
    payment_method   TEXT,
    cashier_name     TEXT,
    _loaded_at       TIMESTAMP DEFAULT NOW(),
    _source_file     TEXT
);

-- ============================================================
-- STAGING LAYER
-- ============================================================
CREATE TABLE staging.sales_clean (
    transaction_id   TEXT PRIMARY KEY,
    sale_date        DATE NOT NULL,
    store_id         TEXT NOT NULL,
    store_name       TEXT,
    product_id       TEXT NOT NULL,
    product_name     TEXT,
    category         TEXT,
    quantity         INTEGER CHECK (quantity > 0),
    unit_price       NUMERIC(10,2) CHECK (unit_price >= 0),
    total_amount     NUMERIC(12,2) CHECK (total_amount >= 0),
    payment_method   TEXT,
    cashier_name     TEXT,
    _cleaned_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_sales_clean_date  ON staging.sales_clean (sale_date);
CREATE INDEX idx_sales_clean_store ON staging.sales_clean (store_id);

CREATE TABLE staging.sales_quarantine (
    transaction_id   TEXT,
    raw_row          JSONB,
    failure_reason   TEXT,
    _quarantined_at  TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- MARTS LAYER
-- ============================================================
CREATE TABLE marts.dim_store (
    store_key        SERIAL PRIMARY KEY,
    store_id         TEXT UNIQUE NOT NULL,
    store_name       TEXT,
    city             TEXT
);

CREATE TABLE marts.dim_product (
    product_key      SERIAL PRIMARY KEY,
    product_id       TEXT UNIQUE NOT NULL,
    product_name     TEXT,
    category         TEXT
);

CREATE TABLE marts.dim_date (
    date_key         DATE PRIMARY KEY,
    year             INTEGER,
    month            INTEGER,
    day              INTEGER,
    day_of_week      TEXT,
    is_weekend       BOOLEAN
);

CREATE TABLE marts.fct_sales (
    sale_key         BIGSERIAL PRIMARY KEY,
    transaction_id   TEXT UNIQUE NOT NULL,
    date_key         DATE REFERENCES marts.dim_date(date_key),
    store_key        INTEGER REFERENCES marts.dim_store(store_key),
    product_key      INTEGER REFERENCES marts.dim_product(product_key),
    quantity         INTEGER,
    unit_price       NUMERIC(10,2),
    total_amount     NUMERIC(12,2),
    payment_method   TEXT
);

CREATE INDEX idx_fct_sales_date  ON marts.fct_sales (date_key);
CREATE INDEX idx_fct_sales_store ON marts.fct_sales (store_key);
