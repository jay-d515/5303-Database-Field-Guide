<details>
<summary>⚙️ Details</summary>

```yaml
is_due: true
id: A02-Performance_Project
name: A02-Performance_Project
title: Comparing SQLite and DuckDB
description: Using a performance tool to benchmark different databases
category: Assignments
date_due:
  month: '12'
  day: '04'
  year: 2026
  hour: 16
```

</details>

# 5303 Database Field Guide

Five database engines, one dataset, one set of questions. You load the same
`store` data into SQLite, DuckDB, PostgreSQL, MongoDB, and Redis, query it
through the same API, measure what each engine does, and decide, with your
own numbers, which engine fits which job.

The goal isn't to write the biggest query. It's to understand why one query
beats another, when two queries are really the same, and why some engines
suit some problems better than others.

## Start here

1. **[setup/](setup/)**: install Git, Python, Docker, QueryMux, and an editor.
2. **[engines/00_foundations/](engines/00_foundations/)**: vocabulary and first SQL.
3. **[engines/01_sqlite/](engines/01_sqlite/)**: the first engine, and the baseline
   every later engine is compared against.

Then [02_duckdb](engines/02_duckdb/) (embedded like SQLite, but stores data
by column), [03_postgres](engines/03_postgres/) (the first server),
[04_mongodb](engines/04_mongodb/), and [05_redis](engines/05_redis/).

## How every unit works

Each engine unit has the same nine sections, so you always know where you
are:

| #   | Section               | Question                                              |
| --- | --------------------- | ----------------------------------------------------- |
| 01  | Why it exists         | What was it built for, and what does it give up?      |
| 02  | Install & verify      | Can I run it and prove it's running?                  |
| 03  | Connect three ways    | The same "hello" from the CLI, QueryMux, and Python   |
| 04  | Model the data        | How does `store` want to look in this engine?         |
| 05  | Load it               | Get the data in, reproducibly                         |
| 06  | Run the query catalog | Q01–Q15 in this engine's language                     |
| 07  | Explain & measure     | What did it do, and how long did it take?             |
| 08  | Concurrency & load    | How does it behave when many requests arrive at once? |
| 09  | When to choose it     | Yes or no on standard scenarios, citing your numbers  |

The setup steps hand you commands. The later sections ask you for something
you can't paste: a prediction, a number, an explanation, or a decision.

## What's where

| Folder / file                     | Holds                                                                      |
| --------------------------------- | -------------------------------------------------------------------------- |
| [setup/](setup/)                  | Install once: Git, Python, Docker, QueryMux, an editor                     |
| [engines/](engines/)              | One folder per engine, nine sections each                                  |
| [tracks/](tracks/)                | Spatial, vector, and distributed comparisons                               |
| [lab/](lab/README.md)             | The measurement API, driver, load test, fairness rules, FINDINGS template  |
| [datasets/](datasets/README.md)   | The `store` data, its query catalog, the generator, and Armageddon         |
| [reference/](reference/README.md) | Look-it-up material: the concept map, patterns, topics, naming conventions |
| [assignments/](assignments/)      | Assignments and the final project                                          |
| [STRUCTURE.md](STRUCTURE.md)      | Naming conventions and where new files go                                  |

## Quick start

Each block starts from the repo root.

```bash
# the classroom database: 1,000 rows, ready in a second
cd engines/01_sqlite/05_load
sqlite3 store_classroom.db ".read rebuild.sql"
```

```bash
# the experiment databases: 10k, 100k, 1m rows, ~10 seconds
python3 datasets/store/generator/make_dbs.py
```

```bash
# the measurement API
cd lab/api/starter_code
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m app.main                                # http://127.0.0.1:8001/docs
```

> **Is this repo in iCloud Drive, Dropbox, or OneDrive?** Keep the generated
> databases out of it: set `DATA_DIR` (see the
> [generator README](datasets/store/generator/README.md)).
