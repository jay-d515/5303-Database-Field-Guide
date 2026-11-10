# Generator

Builds the SQLite experiment databases for the `store` dataset: seeded,
skewed data at three sizes, each in an indexed and an unindexed copy.

```bash
python3 make_dbs.py                  # 10k, 100k, 1m (~10 s, ~290 MB)
python3 make_dbs.py --sizes 10k      # one size, for a quick test
```

Output goes to `../generated/sqlite/`, which is git-ignored. Run it from any
folder. Only the Python standard library is used.

> **Repo in a cloud-synced folder** (iCloud Drive, Dropbox, OneDrive)? Put the
> databases somewhere else. Sync clients copy a live database's files one at
> a time and can corrupt it. Set `DATA_DIR` in your shell profile, and
> `make_dbs.py`, the API, and the driver all use it:
>
> ```bash
> export DATA_DIR="$HOME/5303_data/sqlite"
> ```

| File                | What it does                                                                                   |
| ------------------- | ---------------------------------------------------------------------------------------------- |
| `scale_data.py`     | Builds one database at any size, using [schema.sql](../../../engines/01_sqlite/04_model/schema.sql) |
| `make_dbs.py`       | Calls `scale_data.py` for each size, then makes the `idx_` / `noidx_` pair                     |

For each size, both files hold **identical rows**:

| File              | Indexes                                                                                                  |
| ----------------- | -------------------------------------------------------------------------------------------------------- |
| `idx_<size>.db`   | foreign-key indexes from the schema + [covering_indexes.sql](../../../engines/01_sqlite/05_load/covering_indexes.sql) |
| `noidx_<size>.db` | only `PRIMARY KEY` / `UNIQUE`; [drop_indexes.sql](../../../engines/01_sqlite/05_load/drop_indexes.sql) removes the rest |

Both also get the `monthly_sales` rollup from
[summary_tables.sql](../../../engines/01_sqlite/05_load/summary_tables.sql).

| Size   | Purchases | Customers | Cards (≈) | Products |
| ------ | --------- | --------- | --------- | -------- |
| `10k`  | 10,000    | 500       | 725       | 100      |
| `100k` | 100,000   | 5,000     | 7,500     | 500      |
| `1m`   | 1,000,000 | 50,000    | 75,000    | 5,000    |

There's also a `practice` size (100k purchases) for a throwaway copy you can
break without touching the experiment databases.

## Skew

Purchases concentrate on a few "whale" customers and a few popular products.
About 10% of customers never buy and about 30% of products never sell, so the
anti-join queries (Q08) have real gaps to find. The seed is fixed (1234), so
every student builds the same rows.

> The richer order data for the people_products dataset has its own
> generator: [people_products/generate_orders.py](../../people_products/README.md#generating-orders).
