# `people_products` Dataset (staging)

Raw people and product data that will become the **next version of the
`store` dataset**. It's richer than the current `store` source: more people
in more locations, and products with categories, descriptions, and inventory.

> **Status:** staging. Used by the normalization exercise in
> [SQLite 04_model Part B](../../engines/01_sqlite/04_model/README.md). The
> experiments still use the current [`store`](../store/) dataset until this
> one replaces it.

## Files

| File                                | Rows       | Notes                                                  |
| ----------------------------------- | ---------- | ------------------------------------------------------ |
| `people.csv`                        | 3,000      | Built by `build_people.py` from `people_1`–`_3` (see below) |
| `products.csv`                      | 5,000      | Combined from `products_1`–`_5`; ids renumbered 1–5000 |
| `people_1.csv` … `people_3.csv`     | 1,000 each | Originals; each numbered 1–1000                        |
| `products_1.csv` … `products_5.csv` | 1,000 each | Originals; each numbered 1–1000                        |
| `us_zips.csv`                       | 40,932     | Zip → city, state, county, lat/lon lookup              |
| `build_people.py`                   | —          | Rebuilds `people.csv` from the raw files               |
| `generate_orders.py`                | —          | Generates orders and line items into `generated/`      |

### Building `people.csv`

```bash
python3 build_people.py
```

It's deterministic, so re-running it gives the same file. Starting from the
raw `people_N.csv` files, it:

1. Combines them in file order and renumbers ids 1–3000.
2. Replaces the **349 zips that aren't in `us_zips.csv`** with a real zip
   from the same state. All 3,000 now match the lookup.
3. Resets card expiration dates so **~90% stay valid through 2027-05-31**,
   the end of the academic year. The other ~10% expired between 2025-01 and
   2026-07, inside the order history.

Every other field is unchanged. The raw files and `us_zips.csv` are never
modified.

> **Zips are text.** Excel and the sqlite3 CLI's `.import` both turn `01114`
> into `1114`. Read zips as text, or pad them back to 5 digits.

### Columns

- **people:** `id, fname, lname, credit_card, expiration_date, cvv, email, gender, password, address, state, zip`
- **products:** `id, name, category, sub_category, description, price, inventory`

## Generating orders

```bash
python3 generate_orders.py                 # classroom: 5,000 orders
python3 generate_orders.py --size 100k     # also 10k, 1m
python3 generate_orders.py --size 1m --seed 42
```

Output goes to `generated/<size>/`. The same seed and size always give
byte-identical files. Only `generated/classroom/` is committed; the larger
sizes rebuild in seconds (1m: about 7 s, 75 MB). Rebuild `people.csv` first if
the raw people files change.

| File              | Columns                                               |
| ----------------- | ----------------------------------------------------- |
| `orders.csv`      | `order_id, person_id, order_date, card_last4`         |
| `order_items.csv` | `order_id, line_no, product_id, quantity, unit_price` |

| Size        | Orders    | Item lines (≈) |
| ----------- | --------- | -------------- |
| `classroom` | 5,000     | 9,500          |
| `10k`       | 10,000    | 19,000         |
| `100k`      | 100,000   | 191,000        |
| `1m`        | 1,000,000 | 1.9 million    |

### How the orders behave like real commerce

- **Orders have line items.** One to five per order, usually one. Quantity is
  usually 1.
- **Skewed customers and products.** The top 10% of customers place about a
  third of all orders; the top 10% of products get about 38% of sales.
- **Seasonal.** November and December are busier, weekends a little busier,
  and orders cluster in the daytime.
- **Cards matter.** No order is dated after the customer's card expired.
- **Prices change.** About 10% of products changed price once. Lines before
  the change carry the old price, so `order_items.unit_price` really is a
  snapshot and not a copy of `products.price`.
- **Order ids increase with time**, as in a live system.

## Known issues

| Issue                        | Detail                                                                                                                | Decision                                                                                                                          |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Duplicate products**       | Only 1,759 distinct names across 5,000 rows; 4,644 rows share a name (up to 10 copies), usually identical except `id` | Kept for now. Good material for a "find the duplicates" loading exercise. Must be resolved before `product_name` can be `UNIQUE`. |
| **Sensitive-looking fields** | `password` (plain text), `cvv`, full card numbers                                                                     | Kept in the raw CSV as **test fixtures**, so you can log in as a test user. The database stores only a password hash (login hashes what was typed and compares). PCI rules: a CVV is never stored after authorization, even encrypted; card numbers are tokenized or encrypted. Orders keep only the last 4 digits. |
| People are clean             | No repeated emails or card numbers across the three files                                                             | —                                                                                                                                 |

## Planned use

1. **Normalization exercise:** [SQLite 04_model Part B](../../engines/01_sqlite/04_model/README.md).
2. **The next `store`:** once Part B is due, a reference schema for this data
   can replace the current `store` for the experiments.
3. **New pattern material:** `description` for full-text search (proposed
   Q16) and the vector track; `inventory` for the hot-row load scenario (S3).
