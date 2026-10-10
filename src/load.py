"""
Load step — write clean rows to staging, quarantine to staging,
and build the star schema in the marts layer.
"""
import json
from datetime import datetime

import pandas as pd
from sqlalchemy import text

from src.config import get_engine


def _truncate(engine, table: str) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))


def load_staging_clean(clean_df: pd.DataFrame) -> int:
    """Write clean rows to staging.sales_clean."""
    if clean_df.empty:
        print("⚠️  No clean rows to load.")
        return 0

    engine = get_engine()
    _truncate(engine, "staging.sales_clean")

    out = clean_df[
        [
            "transaction_id", "sale_date", "store_id", "store_name",
            "product_id", "product_name", "category", "quantity",
            "unit_price", "total_amount", "payment_method", "cashier_name",
        ]
    ].copy()
    out["_cleaned_at"] = datetime.now()

    out.to_sql(
        "sales_clean", engine, schema="staging",
        if_exists="append", index=False, method="multi", chunksize=1000,
    )

    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM staging.sales_clean;")).scalar()
    print(f"📤 Loaded {count:,} rows into staging.sales_clean")
    return count


def load_staging_quarantine(quarantine_df: pd.DataFrame) -> int:
    """Write bad rows + reason to staging.sales_quarantine."""
    if quarantine_df.empty:
        print("✅ No rows quarantined.")
        return 0

    engine = get_engine()
    _truncate(engine, "staging.sales_quarantine")

    out = pd.DataFrame({
        "transaction_id": quarantine_df["transaction_id"],
        "raw_row":        quarantine_df.apply(
            lambda r: json.dumps(
                {k: (None if pd.isna(v) else v) for k, v in r.to_dict().items()},
                default=str,
            ),
            axis=1,
        ),
        "failure_reason": quarantine_df["failure_reason"],
        "_quarantined_at": datetime.now(),
    })

    out.to_sql(
        "sales_quarantine", engine, schema="staging",
        if_exists="append", index=False, method="multi", chunksize=1000,
    )

    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM staging.sales_quarantine;")).scalar()
    print(f"⚠️  Quarantined {count:,} rows into staging.sales_quarantine")
    return count


def build_marts(clean_df: pd.DataFrame) -> None:
    """Build the star schema: dim_store, dim_product, dim_date, fct_sales."""
    if clean_df.empty:
        print("⚠️  No data for marts.")
        return

    engine = get_engine()
    for table in ["marts.fct_sales", "marts.dim_date", "marts.dim_product", "marts.dim_store"]:
        _truncate(engine, table)

    # --- dim_store ---
    dim_store = (
        clean_df[["store_id", "store_name"]]
        .drop_duplicates(subset=["store_id"])
        .copy()
    )
    dim_store["city"] = dim_store["store_name"].str.extract(r"([A-Za-z ]+)$")[0].str.strip()
    dim_store.to_sql("dim_store", engine, schema="marts",
                     if_exists="append", index=False)
    print(f"🏬 Built dim_store: {len(dim_store)} stores")

    # --- dim_product ---
    dim_product = (
        clean_df[["product_id", "product_name", "category"]]
        .drop_duplicates(subset=["product_id"])
        .copy()
    )
    dim_product.to_sql("dim_product", engine, schema="marts",
                       if_exists="append", index=False)
    print(f"📦 Built dim_product: {len(dim_product)} products")

    # --- dim_date ---
    dates = pd.to_datetime(clean_df["sale_date"]).dt.normalize().drop_duplicates().sort_values()
    dim_date = pd.DataFrame({"date_key": dates})
    dim_date["year"]        = dim_date["date_key"].dt.year
    dim_date["month"]       = dim_date["date_key"].dt.month
    dim_date["day"]         = dim_date["date_key"].dt.day
    dim_date["day_of_week"] = dim_date["date_key"].dt.day_name()
    dim_date["is_weekend"]  = dim_date["date_key"].dt.dayofweek >= 5
    dim_date.to_sql("dim_date", engine, schema="marts",
                    if_exists="append", index=False)
    print(f"📅 Built dim_date: {len(dim_date)} days")

    # --- fct_sales ---
    # Join keys back from the dims we just loaded
    with engine.connect() as conn:
        store_lookup = pd.read_sql("SELECT store_key, store_id FROM marts.dim_store;", conn)
        product_lookup = pd.read_sql("SELECT product_key, product_id FROM marts.dim_product;", conn)

    fct = clean_df.merge(store_lookup, on="store_id", how="left") \
                  .merge(product_lookup, on="product_id", how="left")

    fct_out = pd.DataFrame({
        "transaction_id": fct["transaction_id"],
        "date_key":       pd.to_datetime(fct["sale_date"]).dt.normalize(),
        "store_key":      fct["store_key"],
        "product_key":    fct["product_key"],
        "quantity":       fct["quantity"],
        "unit_price":     fct["unit_price"],
        "total_amount":   fct["total_amount"],
        "payment_method": fct["payment_method"],
    })

    fct_out.to_sql("fct_sales", engine, schema="marts",
                   if_exists="append", index=False, method="multi", chunksize=1000)
    print(f"💰 Built fct_sales: {len(fct_out):,} sales")


if __name__ == "__main__":
    # Self-test: run the whole chain on the sample
    from src.extract import read_raw_csv
    from src.transform import transform
    from src.quality import apply_quality_rules
    from src.config import RAW_DIR

    raw = read_raw_csv(RAW_DIR / "sales_raw.csv")
    clean_raw = transform(raw)
    clean, quarantined = apply_quality_rules(clean_raw)

    load_staging_clean(clean)
    load_staging_quarantine(quarantined)
    build_marts(clean)
