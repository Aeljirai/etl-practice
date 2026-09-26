"""
Project 01 — Basic ETL
=======================

An ETL (Extract, Transform, Load) pipeline always has these 3 steps:

  EXTRACT   : read raw data from its source (a CSV file here)
  TRANSFORM : clean / normalize / validate the data
  LOAD      : write the clean result to a destination (SQLite here)

Run it with: python etl.py
"""

import re
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

RAW_PATH = Path("data/raw/orders_raw.csv")
DB_PATH = Path("data/output/warehouse.db")

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%Y/%m/%d"]


# ---------------------------------------------------------------------------
# EXTRACT
# ---------------------------------------------------------------------------
def extract(path: Path) -> pd.DataFrame:
    print(f"[EXTRACT] Reading {path}")
    df = pd.read_csv(path, dtype=str)  # everything as str: make NO assumptions about format
    print(f"[EXTRACT] {len(df)} rows read")
    return df


# ---------------------------------------------------------------------------
# TRANSFORM — each function fixes ONE specific problem. This separation is
# what keeps a cleaning pipeline readable and testable.
# ---------------------------------------------------------------------------
def clean_names(df: pd.DataFrame) -> pd.DataFrame:
    df["customer_name"] = df["customer_name"].str.strip().str.title()
    return df


def clean_country(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "morocco": "Morocco", "maroc": "Morocco",
        "france": "France",
        "spain": "Spain",
    }
    df["country"] = (
        df["country"].str.strip().str.lower().map(mapping).fillna(df["country"].str.strip())
    )
    return df


def clean_status(df: pd.DataFrame) -> pd.DataFrame:
    df["status"] = df["status"].str.strip().str.lower()
    return df


def parse_price(raw: str) -> float | None:
    if pd.isna(raw):
        return None
    # strip everything that isn't a digit, dot or comma ($, "USD", spaces...)
    cleaned = re.sub(r"[^0-9.,]", "", str(raw))
    cleaned = cleaned.replace(",", ".")
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def clean_price(df: pd.DataFrame) -> pd.DataFrame:
    df["unit_price"] = df["unit_price"].apply(parse_price)
    return df


def parse_date(raw: str):
    if pd.isna(raw) or raw == "":
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt).date().isoformat()
        except ValueError:
            continue
    return None  # no known format matched


def clean_dates(df: pd.DataFrame) -> pd.DataFrame:
    df["order_date"] = df["order_date"].apply(parse_date)
    return df


def clean_quantity(df: pd.DataFrame) -> pd.DataFrame:
    # a missing quantity is reasonably defaulted to 1 (a business rule worth documenting!)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
    return df


def add_total_amount(df: pd.DataFrame) -> pd.DataFrame:
    df["total_amount"] = (df["unit_price"] * df["quantity"]).round(2)
    return df


def transform(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    print("[TRANSFORM] Cleaning...")

    before = len(df)
    df = df.drop_duplicates()
    print(f"[TRANSFORM] Removed {before - len(df)} exact duplicates")

    df = clean_names(df)
    df = clean_country(df)
    df = clean_status(df)
    df = clean_price(df)
    df = clean_dates(df)
    df = clean_quantity(df)
    df = add_total_amount(df)

    # a row is "invalid" if critical info is still missing after cleaning
    email_present = df["email"].fillna("").str.strip().ne("")
    is_valid = df["unit_price"].notna() & df["order_date"].notna() & email_present
    rejected = df[~is_valid].copy()
    clean_df = df[is_valid].copy()

    print(f"[TRANSFORM] {len(clean_df)} valid rows, {len(rejected)} rejected rows")
    return clean_df, rejected


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------
def load(clean_df: pd.DataFrame, rejected_df: pd.DataFrame, db_path: Path) -> None:
    print(f"[LOAD] Writing to {db_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        clean_df.to_sql("orders", conn, if_exists="replace", index=False)
        rejected_df.to_sql("orders_rejected", conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()
    print(f"[LOAD] Table 'orders': {len(clean_df)} rows | 'orders_rejected': {len(rejected_df)} rows")


def main():
    raw_df = extract(RAW_PATH)
    clean_df, rejected_df = transform(raw_df)
    load(clean_df, rejected_df, DB_PATH)
    print("\n[OK] Pipeline finished. Open data/output/warehouse.db to explore the result.")


if __name__ == "__main__":
    main()
