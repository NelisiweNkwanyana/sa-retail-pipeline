"""
Generates messy raw sales data for the SA Retail Pipeline project.
Simulates data coming from a legacy POS system — intentionally dirty.
"""
import random
import csv
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("en_GB")  # SA flavor via manual STORES/PRODUCTS lists
random.seed(42)        # reproducible data

# SA-specific reference data
STORES = [
    ("JHB-001", "Johannesburg CBD"),
    ("JHB-002", "Sandton City"),
    ("CPT-001", "Cape Town V&A"),
    ("CPT-002", "Canal Walk"),
    ("DBN-001", "Durban Gateway"),
    ("PTA-001", "Pretoria Menlyn"),
]

PRODUCTS = [
    ("P1001", "Wool Blanket",         "Home",     349.99),
    ("P1002", "Rooibos Tea 500g",     "Grocery",   89.50),
    ("P1003", "Biltong 250g",         "Grocery",  129.99),
    ("P1004", "Braai Grid",           "Outdoor",  459.00),
    ("P1005", "Load Shedding Lamp",   "Home",     299.99),
    ("P1006", "Vuvuzela",             "Sports",    75.00),
    ("P1007", "Springbok Jersey",     "Sports",   899.99),
    ("P1008", "Cast Iron Potjie Pot", "Outdoor",  749.50),
    ("P1009", "Mrs Ball's Chutney",   "Grocery",   45.99),
    ("P1010", "Solar Power Bank",     "Home",     599.00),
]

PAYMENT_METHODS = ["card", "CARD", "Cash", "EFT", "cash", "SnapScan"]

def maybe_messy(value, chance=0.05):
    """Randomly corrupt a value to simulate dirty data."""
    r = random.random()
    if r < chance:
        return ""              # missing
    if r < chance * 2:
        return "NULL"          # bad null representation
    return value

def generate_row(row_id, sale_date):
    store_id, store_name = random.choice(STORES)
    product_id, product_name, category, price = random.choice(PRODUCTS)
    qty = random.choice([1, 1, 1, 2, 2, 3, 5, 10])
    total = round(price * qty, 2)

    return {
        "transaction_id": f"TXN{row_id:07d}",
        "sale_date":      sale_date.strftime("%Y/%m/%d"),  # slashes = messy
        "store_id":       maybe_messy(store_id, 0.02),
        "store_name":     store_name,
        "product_id":     maybe_messy(product_id, 0.02),
        "product_name":   product_name,
        "category":       maybe_messy(category, 0.03),
        "quantity":       maybe_messy(qty, 0.02),
        "unit_price":     price,
        "total_amount":   maybe_messy(total, 0.02),
        "payment_method": random.choice(PAYMENT_METHODS),
        "cashier_name":   fake.name(),
    }

def main():
    rows = []
    start = datetime(2024, 1, 1)
    for i in range(1, 5001):  # 5,000 transactions
        days = random.randint(0, 364)
        sale_date = start + timedelta(days=days)
        rows.append(generate_row(i, sale_date))

    # Add ~30 duplicate rows (simulate double-scans)
    for _ in range(30):
        rows.append(random.choice(rows).copy())

    out = "data/raw/sales_raw.csv"
    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Generated {len(rows)} rows -> {out}")

if __name__ == "__main__":
    main()
