"""
Pipeline orchestration — runs the full ETL end-to-end.

Usage:
    python -m src.pipeline
"""
import sys
import time
from datetime import datetime

from src.config import RAW_DIR
from src.extract import read_raw_csv, load_to_raw_layer
from src.transform import transform
from src.quality import apply_quality_rules
from src.load import load_staging_clean, load_staging_quarantine, build_marts


def run_step(name: str, fn, *args, **kwargs):
    """Run one pipeline step with timing and error handling."""
    print(f"\n{'─' * 60}")
    print(f"▶️  {name}")
    print(f"{'─' * 60}")
    start = time.time()

    try:
        result = fn(*args, **kwargs)
    except Exception as e:
        elapsed = time.time() - start
        print(f"❌ {name} FAILED after {elapsed:.2f}s")
        print(f"   Error: {type(e).__name__}: {e}")
        sys.exit(1)

    elapsed = time.time() - start
    print(f"⏱️  {name} completed in {elapsed:.2f}s")
    return result


def run_pipeline() -> None:
    """Run the full ETL pipeline: extract -> transform -> quality -> load."""
    started = datetime.now()
    print("=" * 60)
    print("🏭 SA RETAIL PIPELINE")
    print(f"   Started: {started.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. EXTRACT — read CSV, load into raw layer
    csv_path = RAW_DIR / "sales_raw.csv"
    raw_df = run_step("EXTRACT: read raw CSV", read_raw_csv, csv_path)
    run_step("EXTRACT: load to raw.sales_raw", load_to_raw_layer, raw_df, csv_path.name)

    # 2. TRANSFORM — clean types, dates, dedupe
    clean_raw_df = run_step("TRANSFORM: clean types and dedupe", transform, raw_df)

    # 3. QUALITY — split clean vs quarantine
    clean_df, quarantine_df = run_step(
        "QUALITY: apply data quality rules",
        apply_quality_rules,
        clean_raw_df,
    )

    # 4. LOAD — write staging + build star schema
    run_step("LOAD: staging.sales_clean", load_staging_clean, clean_df)
    run_step("LOAD: staging.sales_quarantine", load_staging_quarantine, quarantine_df)
    run_step("LOAD: marts (star schema)", build_marts, clean_df)

    # Summary
    finished = datetime.now()
    total = (finished - started).total_seconds()
    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETE")
    print(f"   Duration: {total:.2f}s")
    print(f"   Rows in  →  Rows out: {len(raw_df):,}  →  {len(clean_df):,}")
    print(f"   Quarantined: {len(quarantine_df):,}")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
