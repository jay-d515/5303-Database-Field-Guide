# `store` Dataset

The course-wide dataset: 8 normalized tables (plus extras to be chosen), produced by
a seeded, skewed generator at fixed sizes. Every engine loads the **same rows**.

| Size            | Purchases       | Use                    |
| --------------- | --------------- | ---------------------- |
| classroom       | 1k              | Live demos in QueryMux |
| 10k / 100k / 1m | 10k / 100k / 1M | Experiments            |

| File                                 | Purpose                                                     |
| ------------------------------------ | ----------------------------------------------------------- |
| [schema.md](schema.md)               | Tables, keys, relationships, and design rationale           |
| [query_catalog.md](query_catalog.md) | Q01–Q15: engine-neutral intent, pattern tag, per-engine fit |
| `classroom/`                         | `store_flat.csv`: the 1k flat CSV for demos and the ETL lesson (one purchase per customer) |
| [generator/](generator/README.md)    | `make_dbs.py`: builds the SQLite experiment databases       |
| `generated/sqlite/`                  | Output of `make_dbs.py` (git-ignored)                       |
| `loaders/`                           | One loader per engine (planned; SQLite's is [05_load](../../engines/01_sqlite/05_load/README.md)) |
