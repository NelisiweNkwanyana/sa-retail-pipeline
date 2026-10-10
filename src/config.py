"""
Central configuration for the SA Retail pipeline.
Loads DB credentials from .env file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env from project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Database config
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "sa_retail")
DB_USER = os.getenv("POSTGRES_USER", "retail_admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "localdev123")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
QUARANTINE_DIR = DATA_DIR / "quarantine"


def get_engine():
    """Return a SQLAlchemy engine connected to the project database."""
    return create_engine(DATABASE_URL)


if __name__ == "__main__":
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_database(), current_user;"))
        print("✅ Connected:", result.fetchone())
