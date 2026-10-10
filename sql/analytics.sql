-- ============================================================
-- SA Retail Pipeline — Analytics Views
-- Business-facing KPIs for Power BI / Metabase / Looker
-- ============================================================

DROP VIEW IF EXISTS analytics.v_kpi_daily CASCADE;
DROP VIEW IF EXISTS analytics.v_kpi_by_store CASCADE;
DROP VIEW IF EXISTS analytics.v_kpi_by_product CASCADE;
DROP VIEW IF EXISTS analytics.v_kpi_payment_methods CASCADE;
DROP VIEW IF EXISTS analytics.v_top_products CASCADE;

DROP SCHEMA IF EXISTS analytics CASCADE;
CREATE SCHEMA analytics;

-- ============================================================
-- 1. Daily revenue KPIs
-- ============================================================
CREATE VIEW analytics.v_kpi_daily AS
SELECT
    f.date_key                              AS sale_date,
    COUNT(*)                                AS num_transactions,
    SUM(f.quantity)                         AS units_sold,
    ROUND(SUM(f.total_amount), 2)           AS revenue,
    ROUND(AVG(f.total_amount), 2)           AS avg_transaction_value,
    COUNT(DISTINCT f.store_key)             AS active_stores
FROM marts.fct_sales f
GROUP BY f.date_key
ORDER BY f.date_key;

-- ============================================================
-- 2. Revenue by store
-- ============================================================
CREATE VIEW analytics.v_kpi_by_store AS
SELECT
    s.store_id,
    s.store_name,
    COUNT(*)                                AS num_transactions,
    SUM(f.quantity)                         AS units_sold,
    ROUND(SUM(f.total_amount), 2)           AS revenue,
    ROUND(AVG(f.total_amount), 2)           AS avg_transaction_value
FROM marts.fct_sales f
JOIN marts.dim_store s USING (store_key)
GROUP BY s.store_id, s.store_name
ORDER BY revenue DESC;

-- ============================================================
-- 3. Revenue by product category
-- ============================================================
CREATE VIEW analytics.v_kpi_by_product AS
SELECT
    p.category,
    COUNT(*)                                AS num_transactions,
    SUM(f.quantity)                         AS units_sold,
    ROUND(SUM(f.total_amount), 2)           AS revenue,
    ROUND(AVG(f.unit_price), 2)             AS avg_unit_price
FROM marts.fct_sales f
JOIN marts.dim_product p USING (product_key)
GROUP BY p.category
ORDER BY revenue DESC;

-- ============================================================
-- 4. Payment method breakdown
-- ============================================================
CREATE VIEW analytics.v_kpi_payment_methods AS
SELECT
    f.payment_method,
    COUNT(*)                                AS num_transactions,
    ROUND(SUM(f.total_amount), 2)           AS revenue,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_transactions
FROM marts.fct_sales f
GROUP BY f.payment_method
ORDER BY revenue DESC;

-- ============================================================
-- 5. Top 10 products by revenue
-- ============================================================
CREATE VIEW analytics.v_top_products AS
SELECT
    p.product_name,
    p.category,
    SUM(f.quantity)                         AS units_sold,
    ROUND(SUM(f.total_amount), 2)           AS revenue
FROM marts.fct_sales f
JOIN marts.dim_product p USING (product_key)
GROUP BY p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;
