"""
Transform step — clean the messy raw POS data into a typed,
deduplicated DataFrame ready for the staging layer.

Each function does ONE thing. Easy to test, easy to reason about.
"""
import pandas as pd

# Strings that mean "missing" in this legacy export
NULL_STRINGS = {"", "NULL", "null", "N/A", "n/a", "None", "none", " "}


def normalize_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Replace legacy null markers ("NULL", "", whitespace) with real NaN."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(
                lambda v: None if (isinstance(v, str) and v.strip() in NULL_STRINGS) else v
            )
    return df


def clean_types(df: pd.DataFrame) -> pd.DataFrame:
    """Parse dates and cast numeric columns."""
    df = df.copy()

    # Parse date: "2024/11/23" -> datetime
    df["sale_date"] = pd.to_datetime(df["sale_date"], format="%Y/%m/%d", errors="coerce")

    # Cast numeric columns (invalid -> NaN)
    df["quantity"]     = pd.to_numeric(df["quantity"],     errors="coerce")
    df["unit_price"]   = pd.to_numeric(df["unit_price"],   errors="coerce")
    df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")

    return df


def normalize_text(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase payment_method, strip whitespace from all text columns."""
    df = df.copy()

    if "payment_method" in df.columns:
        df["payment_method"] = df["payment_method"].str.lower().str.strip()

    for col in ["store_name", "product_name", "category", "cashier_name"]:
        if col in df.columns:
            df[col] = df[col].str.strip()

    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Keep first occurrence of each transaction_id."""
    before = len(df)
    df = df.drop_duplicates(subset=["transaction_id"], keep="first")
    removed = before - len(df)
    print(f"🧹 Removed {removed} duplicate transaction_id rows")
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Full transform pipeline. Order matters!"""
    print("🔧 Transforming...")

    df = normalize_missing(df)
    df = clean_types(df)
    df = normalize_text(df)
    df = remove_duplicates(df)

    print(f"✅ Transform complete. {len(df):,} clean rows.")
    return df


if __name__ == "__main__":
    # Quick self-test with a tiny sample
    sample = pd.DataFrame({
        "transaction_id": ["T1", "T2", "T3", "T1"],
        "sale_date":      ["2024/11/23", "2024/08/04", "bad-date", "2024/11/23"],
        "quantity":       ["2", "NULL", "", "2"],
        "unit_price":     ["349.99", "129.99", "45.99", "349.99"],
        "total_amount":   ["699.98", "129.99", "45.99", "699.98"],
        "payment_method": ["cash", "CARD", "Cash ", "cash"],
        "store_name":     [" JHB CBD ", "CPT V&A", "DBN", " JHB CBD "],
        "product_name":   ["Wool Blanket", "Biltong", "Chutney", "Wool Blanket"],
        "category":       ["Home", "Grocery", "Grocery", "Home"],
        "cashier_name":   ["A", "B", "C", "A"],
        "store_id":       ["JHB-001", "CPT-001", "DBN-001", "JHB-001"],
        "product_id":     ["P1001", "P1003", "P1009", "P1001"],
    })
    out = transform(sample)
    print(out.to_string())
