"""
Quality step — apply data quality rules, split good rows from bad.

Good rows -> return for loading into staging.sales_clean
Bad rows  -> log the reason, return for loading into staging.sales_quarantine
"""
import pandas as pd


def apply_quality_rules(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (clean_df, quarantine_df).

    A row is quarantined if it fails ANY rule. The failure_reason column
    describes every rule it failed (comma-separated).
    """
    df = df.copy()

    # Build a DataFrame of rule results: True = failed
    rules = pd.DataFrame(index=df.index)

    rules["transaction_id_missing"] = df["transaction_id"].isna()
    rules["sale_date_invalid"]      = df["sale_date"].isna()
    rules["store_id_missing"]       = df["store_id"].isna()
    rules["product_id_missing"]     = df["product_id"].isna()
    rules["quantity_invalid"]       = df["quantity"].isna() | (df["quantity"] <= 0)
    rules["total_amount_invalid"]   = df["total_amount"].isna() | (df["total_amount"] < 0)

    # A row fails if any rule is True
    failed_mask = rules.any(axis=1)

    clean_df = df[~failed_mask].copy()

    # For quarantine rows, build a comma-separated reason string
    quarantine_df = df[failed_mask].copy()
    quarantine_df["failure_reason"] = rules[failed_mask].apply(
        lambda row: ", ".join(row.index[row].tolist()),
        axis=1,
    )

    print(f"✅ Passed quality checks: {len(clean_df):,} rows")
    print(f"⚠️  Quarantined:           {len(quarantine_df):,} rows")

    if len(quarantine_df) > 0:
        # Show the breakdown by reason
        print("\n📊 Quarantine breakdown:")
        reason_counts = (
            quarantine_df["failure_reason"]
            .str.split(", ")
            .explode()
            .value_counts()
        )
        for reason, count in reason_counts.items():
            print(f"   {reason}: {count}")

    return clean_df, quarantine_df


if __name__ == "__main__":
    # Self-test with deliberately bad rows
    sample = pd.DataFrame({
        "transaction_id": ["T1", "T2", "T3", None, "T5"],
        "sale_date":      pd.to_datetime(["2024-11-23", "2024-08-04", None, "2024-01-01", "2024-06-15"]),
        "quantity":       [2.0, 1.0, 3.0, 1.0, -5.0],
        "unit_price":     [349.99, 129.99, 45.99, 599.0, 100.0],
        "total_amount":   [699.98, 129.99, 137.97, 599.0, -500.0],
        "payment_method": ["cash", "card", "cash", "eft", "cash"],
        "store_id":       ["JHB-001", "CPT-001", "DBN-001", "JHB-001", "CPT-002"],
        "product_id":     ["P1001", "P1003", "P1009", "P1010", "P1005"],
        "store_name":     ["JHB", "CPT", "DBN", "JHB", "CPT"],
        "product_name":   ["A", "B", "C", "D", "E"],
        "category":       ["X", "Y", "Z", "X", "Y"],
        "cashier_name":   ["A", "B", "C", "D", "E"],
    })

    clean, quarantined = apply_quality_rules(sample)

    print("\n=== CLEAN ROWS ===")
    print(clean[["transaction_id", "sale_date", "quantity", "total_amount"]].to_string(index=False))

    print("\n=== QUARANTINED ROWS ===")
    print(quarantined[["transaction_id", "sale_date", "quantity", "total_amount", "failure_reason"]].to_string(index=False))
