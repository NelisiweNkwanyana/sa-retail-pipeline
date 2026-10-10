"""
Streamlit dashboard for the SA Retail Pipeline.
Reads from analytics.* views and renders interactive KPIs.

Run: streamlit run src/dashboard.py
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path (Streamlit runs from a different cwd)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

from src.config import get_engine


st.set_page_config(
    page_title="Mzansi Retail Dashboard",
    page_icon="🛒",
    layout="wide",
)


@st.cache_data(ttl=60)
def query(sql: str) -> pd.DataFrame:
    """Query Postgres with 60s cache."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)


# ---------- Header ----------
st.title("🛒 Mzansi Retail — Sales Analytics")
st.caption(
    "End-to-end data pipeline: messy POS → PostgreSQL → star schema → analytics views"
)

# ---------- KPI Tiles ----------
kpis = query("""
    SELECT
        SUM(num_transactions) AS txns,
        SUM(units_sold)       AS units,
        SUM(revenue)          AS revenue,
        ROUND(AVG(avg_transaction_value), 2) AS avg_txn
    FROM analytics.v_kpi_daily
""").iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Transactions", f"{int(kpis.txns):,}")
col2.metric("Units Sold", f"{int(kpis.units):,}")
col3.metric("Revenue", f"R {kpis.revenue:,.0f}")
col4.metric("Avg Txn Value", f"R {kpis.avg_txn:,.2f}")

st.divider()

# ---------- Row 1: Revenue over time ----------
st.subheader("📈 Revenue Over Time")
daily = query("SELECT * FROM analytics.v_kpi_daily ORDER BY sale_date")
fig = px.line(
    daily, x="sale_date", y="revenue",
    labels={"sale_date": "Date", "revenue": "Revenue (R)"},
    title=None,
)
fig.update_traces(line_color="#1f77b4")
st.plotly_chart(fig, use_container_width=True)

# ---------- Row 2: Store + Category ----------
left, right = st.columns(2)

with left:
    st.subheader("🏬 Revenue by Store")
    stores = query("SELECT * FROM analytics.v_kpi_by_store")
    stores = stores[stores["store_id"].notna() & (stores["store_id"] != "")]
    fig = px.bar(
        stores.sort_values("revenue", ascending=True),
        x="revenue", y="store_name", orientation="h",
        labels={"revenue": "Revenue (R)", "store_name": ""},
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("📦 Revenue by Category")
    cats = query("SELECT * FROM analytics.v_kpi_by_product")
    fig = px.pie(
        cats, names="category", values="revenue", hole=0.4,
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------- Row 3: Payment + Top Products ----------
left, right = st.columns(2)

with left:
    st.subheader("💳 Payment Methods")
    pay = query("SELECT * FROM analytics.v_kpi_payment_methods")
    fig = px.bar(
        pay, x="payment_method", y="revenue",
        labels={"payment_method": "", "revenue": "Revenue (R)"},
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("🏆 Top 10 Products")
    top = query("SELECT * FROM analytics.v_top_products")
    st.dataframe(
        top,
        use_container_width=True,
        hide_index=True,
        column_config={
            "revenue": st.column_config.NumberColumn("Revenue (R)", format="R %.2f"),
        },
    )

# ---------- Footer ----------
st.divider()
st.caption(
    "Built with Python · pandas · SQLAlchemy · PostgreSQL · Streamlit · Plotly"
)
