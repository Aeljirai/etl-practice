# Sample Project  — Basic ETL (Introduction to data engineering )

## The concept

**ETL** (Extract, Transform, Load) is the oldest and most fundamental pattern
in data engineering. Almost every data pipeline, no matter how fancy the tools
get later (Airflow, Spark, dbt...), is fundamentally doing this:

1. **Extract** — pull raw data from a source (a file, a database, an API...)
2. **Transform** — clean it, reshape it, enrich it, validate it
3. **Load** — write the result somewhere useful (a database, a warehouse...)

Real-world raw data is messy. In this project, you'll deal with the classic
offenders:
- Inconsistent casing (`morocco`, `MOROCCO`, `Morocco`)
- Multiple date formats mixed in the same column
- Prices as strings with currency symbols (`$19.9`) or European decimal commas (`19,9`)
- Missing values (empty quantity, empty email)
- Exact duplicate rows (e.g. from a double form submission)

A data engineer's job is rarely to write the "happy path" logic — it's to
handle all of this mess reliably and predictably.

## Files

- `generate_data.py` — generates the dirty input file `data/raw/orders_raw.csv`
- `etl.py` — the actual pipeline: `extract()` → `transform()` → `load()`
- `data/raw/` — raw input (generated)
- `data/output/warehouse.db` — SQLite database produced by the pipeline

## How to run it

```bash
python generate_data.py   # creates the messy CSV
python etl.py              # runs the ETL pipeline
```

Then explore the result:

```bash
python -c "import sqlite3, pandas as pd; print(pd.read_sql('SELECT * FROM orders LIMIT 10', sqlite3.connect('data/output/warehouse.db')))"
```

Or open `data/output/warehouse.db` with any SQLite browser (e.g. [DB Browser for SQLite](https://sqlitebrowser.org/)).

## What to notice in the code

- Each cleaning concern is its **own small function** (`clean_names`, `clean_price`,
  `clean_dates`...). This is deliberate: a pipeline that mixes 10 cleaning
  rules into one giant block is impossible to debug when something goes wrong.
- The pipeline **never silently drops bad rows** — invalid rows go into an
  `orders_rejected` table instead of disappearing. In production this is
  critical: someone always eventually asks "why is this order missing?" and
  you need an answer.
- Data is read with `dtype=str` in `extract()`. This is intentional — never
  let a library guess types for you on ingestion; you decide the types
  explicitly during `transform()`.

## Exercises

Try these once you've read and understood `etl.py`. Ask me to review your changes.

1. **Add a new cleaning rule**: some `status` values might have trailing
   punctuation or typos (simulate a couple in `generate_data.py`) — clean them.
2. **Tighten validation**: currently a row is rejected only if price, date, or
   email is missing. Add a rule: reject rows where `quantity <= 0` or
   `unit_price <= 0`, and check `orders_rejected` grows accordingly.
3. **Add a summary report**: after loading, print a small report — total
   revenue (`sum(total_amount)`) per country, and per status. Compare
   `completed` vs `cancelled`/`refunded` revenue.
4. **Make it idempotent**: run `python etl.py` twice in a row. Does anything
   break or duplicate? (Hint: look at `if_exists="replace"` — what would
   happen with `if_exists="append"` instead, and why might a real pipeline
   need to think carefully about this?)
5. **Bonus — bad date detection**: add a date format to `generate_data.py`
   that `parse_date()` doesn't know about (e.g. `"Jan 5, 2025"`), rerun
   everything, and confirm those rows land in `orders_rejected` instead of
   crashing the pipeline.

When you're done, tell me what you found — especially for exercise 4, which
touches a concept (**idempotency**) that becomes very important once we add
scheduling/orchestration in project 03.

## Next project

Once you're comfortable here, we move to **02 — Relational modeling +
PostgreSQL**, where instead of dumping everything into one flat table, you'll
design a proper normalized schema (customers, products, orders as separate
tables with foreign keys) and load into a real database server via Docker.
