"""Synthetic data generation, cleaning, and loading for the dashboard."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "ecommerce_orders_raw.csv"
CLEAN_DATA_PATH = DATA_DIR / "ecommerce_orders.csv"

PRODUCTS = {
    "Electronics": {
        "Wireless Headphones": 3_999,
        "Smart Watch": 5_499,
        "Bluetooth Speaker": 2_499,
        "Smartphone": 18_999,
        "Laptop": 54_999,
        "Power Bank": 1_499,
    },
    "Fashion": {
        "Sneakers": 3_299,
        "Backpack": 1_799,
        "Denim Jacket": 2_499,
        "Cotton T-Shirt": 799,
        "Running Shoes": 4_299,
    },
    "Home & Kitchen": {
        "Air Fryer": 6_499,
        "Coffee Maker": 3_499,
        "Cookware Set": 4_999,
        "Desk Lamp": 1_299,
        "Bedsheet Set": 1_999,
    },
    "Beauty": {
        "Face Serum": 899,
        "Skincare Kit": 1_799,
        "Hair Dryer": 2_999,
        "Perfume": 2_499,
    },
    "Books": {
        "Business Bestseller": 599,
        "Python Programming": 899,
        "Mystery Novel": 399,
        "Personal Finance Guide": 499,
    },
}

REGIONS = ("North", "South", "East", "West", "Central")
PAYMENT_MODES = ("COD", "Online", "Card", "Wallet")
ORDER_STATUSES = ("Delivered", "Returned", "Cancelled", "Pending")
RAW_COLUMNS = (
    "order_id",
    "order_date",
    "customer_id",
    "product",
    "category",
    "quantity",
    "unit_price",
    "discount_pct",
    "cost",
    "region",
    "payment_mode",
    "order_status",
)


def generate_raw_data(rows: int = 3_600, seed: int = 42) -> pd.DataFrame:
    """Create reproducible order data with realistic, intentional quality issues."""
    rng = np.random.default_rng(seed)
    products = [
        (category, product, price)
        for category, category_products in PRODUCTS.items()
        for product, price in category_products.items()
    ]
    customer_weights = 1 / np.arange(1, 1_201, dtype=float) ** 0.72
    customer_weights /= customer_weights.sum()
    records: list[dict[str, object]] = []

    for index in range(rows):
        category, product, base_price = products[int(rng.integers(0, len(products)))]
        year = int(rng.choice((2023, 2024, 2025)))
        day_of_year = int(rng.integers(0, 366 if year == 2024 else 365))
        order_date = pd.Timestamp(year, 1, 1) + pd.Timedelta(days=day_of_year)
        month = order_date.month
        seasonal_factor = 1.22 if month in (10, 11, 12) else 0.94 if month in (2, 3) else 1.0
        unit_price = round(float(base_price * seasonal_factor * rng.uniform(0.9, 1.12)), 2)
        quantity = int(rng.choice((1, 2, 3, 4), p=(0.61, 0.25, 0.10, 0.04)))
        discount_pct = round(float(rng.choice(
            (0, 0.05, 0.10, 0.15, 0.20, 0.25),
            p=(0.24, 0.20, 0.22, 0.18, 0.11, 0.05),
        )), 2)
        cost = round(unit_price * quantity * float(rng.uniform(0.52, 0.78)), 2)
        customer_number = int(rng.choice(np.arange(1, 1_201), p=customer_weights))
        status = str(rng.choice(ORDER_STATUSES, p=(0.76, 0.08, 0.08, 0.08)))
        region = str(rng.choice(REGIONS, p=(0.25, 0.23, 0.15, 0.22, 0.15)))
        category_value = str(rng.choice((category, category.lower(), category.upper())))

        records.append({
            "order_id": f"ORD{index + 1:05d}",
            "order_date": order_date.strftime("%Y-%m-%d"),
            "customer_id": f"CUST{customer_number:04d}",
            "product": product,
            "category": category_value,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount_pct": discount_pct,
            "cost": cost,
            "region": region,
            "payment_mode": str(rng.choice(PAYMENT_MODES, p=(0.36, 0.36, 0.20, 0.08))),
            "order_status": status,
        })

    raw = pd.DataFrame.from_records(records, columns=RAW_COLUMNS)

    # Keep a small number of deterministic, visible data-quality issues for the
    # cleaning exercise without making the generated dataset unpredictable.
    raw.loc[5, "quantity"] = -2
    raw.loc[12, "order_date"] = "not-a-date"
    raw.loc[20, "customer_id"] = " cust0001 "
    raw.loc[27, "region"] = None
    raw.loc[31, "discount_pct"] = 1.4
    raw.loc[42, "unit_price"] = None
    raw.loc[56, "product"] = "  " + str(raw.loc[56, "product"]) + "  "
    raw.loc[73, "category"] = "electronics"
    raw.loc[88, "cost"] = None
    raw.loc[104, "payment_mode"] = None
    raw = pd.concat([raw, raw.iloc[[0, 1]]], ignore_index=True)
    return raw


def clean_orders(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalize source data and return validated, analysis-ready order records."""
    missing_columns = set(RAW_COLUMNS).difference(raw.columns)
    if missing_columns:
        raise ValueError(f"Dataset is missing required columns: {', '.join(sorted(missing_columns))}")

    orders = raw.loc[:, list(RAW_COLUMNS)].copy()
    orders["order_id"] = orders["order_id"].astype("string").str.strip().str.upper()
    orders["customer_id"] = orders["customer_id"].astype("string").str.strip().str.upper()
    for column in ("product", "category", "region", "payment_mode", "order_status"):
        orders[column] = orders[column].astype("string").str.strip()

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce", format="mixed")
    for column in ("quantity", "unit_price", "discount_pct", "cost"):
        orders[column] = pd.to_numeric(orders[column], errors="coerce")

    category_lookup = {name.casefold(): name for name in PRODUCTS}
    orders["category"] = orders["category"].str.casefold().map(category_lookup).fillna("Other")
    for column, default in (
        ("product", "Unknown product"),
        ("region", "Unknown"),
        ("payment_mode", "Unknown"),
        ("order_status", "Unknown"),
        ("customer_id", "UNKNOWN"),
    ):
        orders[column] = orders[column].fillna(default).replace("", default)

    orders["quantity"] = orders["quantity"].fillna(1).clip(lower=1).round().astype(int)
    orders["unit_price"] = orders["unit_price"].replace([np.inf, -np.inf], np.nan)
    orders["cost"] = orders["cost"].replace([np.inf, -np.inf], np.nan)
    orders["discount_pct"] = (
        orders["discount_pct"]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0)
        .clip(lower=0, upper=0.8)
    )
    orders["cost"] = orders["cost"].fillna(orders["unit_price"] * orders["quantity"] * 0.65)

    orders = orders.dropna(subset=["order_id", "order_date", "unit_price"])
    orders = orders.loc[(orders["order_id"] != "") & (orders["unit_price"] > 0)]
    orders = orders.drop_duplicates(subset="order_id", keep="first").copy()
    orders["cost"] = orders["cost"].clip(lower=0)
    orders["sales"] = (orders["unit_price"] * orders["quantity"] * (1 - orders["discount_pct"])).round(2)
    orders["profit"] = (orders["sales"] - orders["cost"]).round(2)
    orders["profit_margin_pct"] = np.where(
        orders["sales"] > 0,
        orders["profit"] / orders["sales"] * 100,
        0,
    ).round(2)
    orders["year"] = orders["order_date"].dt.year.astype(int)
    orders["month"] = orders["order_date"].dt.month.astype(int)
    orders["month_name"] = orders["order_date"].dt.strftime("%b")
    orders["quarter"] = orders["order_date"].dt.quarter.astype(int)
    orders["discount_range"] = pd.cut(
        orders["discount_pct"],
        bins=(-0.001, 0.05, 0.10, 0.15, 0.20, 0.801),
        labels=("0-5%", "5-10%", "10-15%", "15-20%", "20%+"),
        include_lowest=True,
    ).astype("string")

    columns = [
        "order_id",
        "order_date",
        "year",
        "month",
        "month_name",
        "quarter",
        "customer_id",
        "product",
        "category",
        "quantity",
        "unit_price",
        "discount_pct",
        "discount_range",
        "sales",
        "cost",
        "profit",
        "profit_margin_pct",
        "region",
        "payment_mode",
        "order_status",
    ]
    return orders.loc[:, columns].sort_values("order_date").reset_index(drop=True)


def load_raw_orders(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Load the original source file, creating the reproducible sample if needed."""
    if path.exists():
        return pd.read_csv(path)
    return generate_raw_data()


def load_orders(path: Path = CLEAN_DATA_PATH) -> pd.DataFrame:
    """Load the clean dataset, deriving it from the raw source when necessary."""
    if path.exists():
        orders = pd.read_csv(path, parse_dates=["order_date"])
        if "discount_range" in orders.columns:
            orders["discount_range"] = orders["discount_range"].astype("string")
        return orders
    raw = load_raw_orders()
    return clean_orders(raw)


def save_sample_data() -> tuple[Path, Path]:
    """Generate and save both the deliberately messy source and clean dataset."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw = generate_raw_data()
    cleaned = clean_orders(raw)
    raw.to_csv(RAW_DATA_PATH, index=False)
    cleaned.to_csv(CLEAN_DATA_PATH, index=False)
    return RAW_DATA_PATH, CLEAN_DATA_PATH
