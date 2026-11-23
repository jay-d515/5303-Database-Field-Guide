# Completed structure: Redis Caching

Assignment: [assignments/Caching_Project](../../assignments/caching_project/README.md)

This folder is what `Caching_Project/` in your course repo should look like
when you're done. Every file here holds only a description of what belongs
in it: no answers, no solution code, and no measured numbers.

The handout's deliverables (section 11) ask for the application source, a
database setup script, a dependency list, instructions for running the
experiment, and a `README.md` report with results, at least one graph, and a
measured conclusion.

## The structure

```
Caching_Project/
├── README.md                  (required)  your report: how to run, results, graph, hits/misses, discussion, conclusion
├── requirements.txt           (required)  the dependency list
├── setup_db.py                (required)  builds shop.db (500,000 purchases)
├── main.py                    (required)  FastAPI app: no-cache, Redis, dictionary cache, simple + expensive queries
├── benchmark.py               (required*) sends N requests, records latency / p95 / req/s / hits / misses
├── make_graphs.py             (recommended) results/*.csv -> graphs/*.png
├── .gitignore
├── results/                   (required*) raw measurements, one file per lab part
│   ├── part_a_baseline.csv
│   ├── part_b_redis.csv            cold vs. warm cache
│   ├── part_c_ttl.csv              5 s, 30 s, 60 s
│   ├── part_d_dict_vs_redis.csv
│   └── part_e_query_complexity.csv simple indexed lookup vs. aggregation
├── graphs/                    (required)  at least one .png comparing performance
└── extension/                 (optional)  graduate extension and extra credit
    ├── README.md                   multi-worker comparison + stampede write-up
    └── stampede.py                 reproduce the stampede, measure the fix
```

\* The assignment requires the measurements, not these exact files. See
*Acceptable variations* for other ways to produce and store them.

## How the files map to the assignment

| Lab part             | Code                                          | Data                          | Write-up (in your `README.md`)         |
| -------------------- | --------------------------------------------- | ----------------------------- | -------------------------------------- |
| A · Baseline         | no-cache route in `main.py`                   | `part_a_baseline.csv`         | *Part A*                               |
| B · Redis caching    | cache-aside route in `main.py`                | `part_b_redis.csv`            | *Part B*, *Cache hits and misses*      |
| C · TTL experiment   | configurable TTL in `main.py`                 | `part_c_ttl.csv`              | *Part C*                               |
| D · Dictionary cache | dictionary cache with expiration in `main.py` | `part_d_dict_vs_redis.csv`    | *Part D*                               |
| E · Query complexity | indexed lookup + aggregation, `sleep` removed | `part_e_query_complexity.csv` | *Part E*                               |
| F · Analysis         | `make_graphs.py`                              | `graphs/`                     | *Part F* table, *Does the model hold?* |
| §10 · Discussion     | —                                             | —                             | *Discussion questions*                 |
| Grad extension       | `extension/stampede.py`, `--workers` runs     | extra CSVs                    | `extension/README.md`                  |

## Your `README.md`

The file you're reading explains the structure. **Your** `README.md` in this
spot is the report, and it's most of the grade. Use these sections, in this
order:

| Section                        | What goes in it                                                                                                                                                  |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| How to run the experiment      | Everything needed to reproduce your numbers, in order: venv, `requirements.txt`, start Redis, `setup_db.py`, start the API, run the benchmarks, build the graphs |
| Environment                    | Machine, OS, Python version, Redis version, Docker or not                                                                                                        |
| Caching strategies implemented | One short paragraph each: no cache, Redis cache-aside, dictionary cache with expiration                                                                          |
| Results                        | A subsection per lab part, A through E                                                                                                                           |
| Part F: Summary table          | The table below, filled in, plus at least one embedded graph, e.g. `![Latency by strategy](graphs/latency_by_strategy.png)`                                      |
| Cache hits and misses          | What you observed and why: cold start, expirations, invalidation                                                                                                 |
| Does the model hold?           | Your measurements against the model in handout section 3.1                                                                                                       |
| When was Redis beneficial?     | The conditions, from your numbers                                                                                                                                |
| Discussion questions           | The ten questions in handout section 10, citing your numbers where you can                                                                                       |
| Conclusion                     | Supported by measurements, not assumptions                                                                                                                       |

The Part F table:

| Strategy          | Avg. Latency | p95 Latency | Requests/sec | Hit Rate |
| ----------------- | ------------ | ----------- | ------------ | -------- |
| No cache          |              |             |              | N/A      |
| Python dictionary |              |             |              |          |
| Redis, 5s TTL     |              |             |              |          |
| Redis, 30s TTL    |              |             |              |          |
| Redis, 60s TTL    |              |             |              |          |

## Acceptable variations

**Application layout**

| Variation                  | Looks like                                                                                                                     |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| One file (shown)           | Everything in `main.py`: simplest, and fine at this size                                                                       |
| Split modules              | `main.py` (routes) + `cache.py` (Redis and dictionary caches) + `db.py` (queries)                                              |
| Package                    | `app/main.py`, `app/cache.py`, ... run with `uvicorn app.main:app`                                                             |
| Separate apps per strategy | `main_nocache.py`, `main_redis.py`, `main_dict.py`. This works, but a single app with separate routes makes comparisons fairer |

**Measuring**

| Variation             | Looks like                                                                                                                          |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| Python script (shown) | `benchmark.py` using `httpx`, `requests`, or `aiohttp`                                                                              |
| Shell + curl          | `benchmark.sh` looping over `curl -w "%{time_total}"`, writing to `results/`                                                        |
| Locust                | `locustfile.py` + Locust's exported CSVs (`*_stats.csv`) in `results/`                                                              |
| k6                    | `load_test.js` + its JSON or summary output in `results/`                                                                           |
| Notebook              | `analysis.ipynb` that runs or loads the benchmarks and draws the graphs (replaces `make_graphs.py`). Commit it with outputs visible |

**Results files.** One CSV per part (shown), one combined `results.csv` with
a `part` column, or JSON. Column names are up to you; the CSV headers here
are suggestions. What matters is that every number in your README table can
be traced back to a raw file.

**Running Redis.** The handout's `docker run` command in your README is
enough. A `compose.yml` (or `docker-compose.yml`) that starts Redis is a
nice addition, especially for the multi-worker extension.

**Database.** SQLite is the default. If you substituted PostgreSQL, expect
a `compose.yml` for it, a `.env.example` with placeholder credentials, and
a `setup_db.py` that loads Postgres instead.

**Discussion questions.** In your README (shown) or in a separate
`DISCUSSION.md` linked from the README.

## What must NOT be in the folder

- `shop.db` (rebuild it with `setup_db.py`) and Redis's `dump.rdb`
- `.venv/`, `venv/`, `__pycache__/`
- A `.env` with real credentials (commit `.env.example` instead)
- `.DS_Store`

The `.gitignore` here covers them; copy it if you don't have one.

## Common mistakes the structure helps you catch

- A README table with numbers but no `results/` files behind them.
- No graph, or a graph that isn't embedded or linked in the README.
- A dictionary cache that never expires, compared with a Redis cache that
  does (Part D asks for comparable expiration).
- Part E still running with `time.sleep()` in the query.

## Check your folder

The field guide's [check_completed.py](../../check_completed.py) compares
your folder with this one and looks inside each file for work of your own.
Run it from your course repo:

```bash
cd ~/5303/my-repo
python ~/5303/5303-Database-Field-Guide/check_completed.py caching
```

✅ means the file is there with content of your own, 🟡 is worth a look,
❌ is missing or still the template, and ⚪ is optional. It checks that your
work is **there**, not that it's **right**.
