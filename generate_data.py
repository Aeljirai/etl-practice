"""
Generates a "dirty" CSV file that mimics real e-commerce order data.

Why dirty? Because in real life, raw data ALWAYS has problems: missing values,
duplicates, inconsistent date formats, mixed casing, currency symbols, stray
whitespace... A data engineer's job starts with cleaning this up before anyone
can analyze it.
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

FIRST_NAMES = ["Amine", "Sara", "Youssef", "Nadia", "Karim", "Lina", "Omar", "Hind", "Yassine", "Salma"]
LAST_NAMES = ["Benali", "Idrissi", "Mansouri", "Zahra", "Cherkaoui", "Alaoui", "Bakkali", "Fassi"]
COUNTRIES = ["Morocco", "morocco", "MAROC", "France", "france", "Spain", "SPAIN", " Morocco"]
PRODUCTS = [
    ("Laptop Pro 14", 899.99),
    ("Wireless Mouse", 19.90),
    ("USB-C Hub", 34.50),
    ("Mechanical Keyboard", 79.00),
    ("27in Monitor", 249.00),
    ("Noise Cancelling Headphones", 129.99),
    ("Webcam HD", 45.00),
    ("Desk Lamp", 22.30),
]
STATUSES = ["completed", "Completed", "COMPLETED", "cancelled", "pending", "refunded"]

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%Y/%m/%d"]


def random_date():
    start = datetime(2025, 1, 1)
    delta_days = random.randint(0, 270)
    d = start + timedelta(days=delta_days)
    fmt = random.choice(DATE_FORMATS)
    return d.strftime(fmt)


def make_row(order_id):
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    # random casing on the name, just like a poorly validated web form
    name = random.choice([f"{first} {last}", f"{first.upper()} {last.upper()}", f"{first.lower()} {last.lower()}"])

    product, unit_price = random.choice(PRODUCTS)
    qty = random.choice([1, 1, 1, 2, 2, 3, None])  # None = missing value
    country = random.choice(COUNTRIES)
    status = random.choice(STATUSES)

    # price sometimes with a currency symbol or decimal comma (classic Excel export)
    price_str = random.choice([
        f"{unit_price}",
        f"${unit_price}",
        f"{unit_price} USD",
        f"{str(unit_price).replace('.', ',')}",
    ])

    email = f"{first.lower()}.{last.lower()}@example.com" if random.random() > 0.05 else ""

    return {
        "order_id": order_id,
        "customer_name": name,
        "email": email,
        "country": country,
        "product": product,
        "unit_price": price_str,
        "quantity": qty if qty is not None else "",
        "order_date": random_date(),
        "status": status,
    }


def main():
    rows = []
    for i in range(1, 501):
        rows.append(make_row(i))

    # inject exact duplicates on purpose, like a double form submission
    duplicates = random.sample(rows, 15)
    rows.extend(duplicates)
    random.shuffle(rows)

    out_path = "data/raw/orders_raw.csv"
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} rows in {out_path} ({len(duplicates)} intentional duplicates)")


if __name__ == "__main__":
    main()
