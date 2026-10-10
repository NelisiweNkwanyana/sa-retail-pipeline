"""
Extract step — read raw POS CSV and load it into raw.sales_raw.
Preserves all messiness. No cleaning here.
"""
import sys
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy import text

from src.config import RAW_DIR, get_engine


def read_raw_csv(csv_path: Path) -> pd.DataFrame:
    """Read the raw POS CSV as strings — we do NOT clean here."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw file not found: {csv_path}")

    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    print(f"📥 Read {len(df):,} rows from {csv_path.name}")
    return df


def load_to_raw_layer(df: pd.DataFrame, source_file: str) -> int:
    """Insert the DataFrame into raw.sales_raw as-is."""
    df = df.copy()
    df["_source_file"] = source_file
    df["_loaded_at"] = datetime.now()

    engine = get_engine()

    # Clear raw layer first (idempotent re-runs)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE raw.sales_raw;"))

    df.to_sql(
        "sales_raw",
        engine,
        schema="raw",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )

    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM raw.sales_raw;")).scalar()

    print(f"📤 Loaded {count:,} rows into raw.sales_raw")
    return count


def run() -> None:
    csv_path = RAW_DIR / "sales_raw.csv"
    df = read_raw_csv(csv_path)
    load_to_raw_layer(df, source_file=csv_path.name)
    print("✅ Extract step complete.")


if __name__ == "__main__":
    run()
