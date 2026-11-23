# Completed structure: Performance Project (SQLite vs. DuckDB)

Assignment: [assignments/Performance_Project](../../assignments/performance_project/README.md)

This folder is what `Performance_Project/` in your course repo should look
like once the SQLite and DuckDB units are finished. It sits beside your other
assignment folders; the project doesn't need a repo of its own. Every file
here holds only a description of what belongs in it: no answers, no
solution code, and no measured numbers.

Your clone of the field guide stays separate and unedited: it's the course
materials, not your submission (see
[setup/git_github.md](../../assignments/performance_project/setup/git_github.md)).

## The structure

```
Performance_Project/
├── README.md                    (required)  index: your machine, DATA_DIR, links to each FINDINGS
├── .gitignore                   (required)  keeps databases, exports, and .venv out
│
├── sqlite/                      unit 01
│   ├── FINDINGS_sqlite.md       (required)  the course template, filled in: §7, §8, §9
│   ├── 01_why.md                (required)  one paragraph
│   ├── 02_install.md            (required)  the three verify outputs
│   ├── 03_connect.md            (required)  hello from CLI, QueryMux, Python
│   ├── 04_model.md              (required)  B1 grouping, how it changed, row counts, 3 decisions
│   ├── your_turn_checks.sql     (required)  your copy, all 22 checks completed
│   ├── my_schema.sql            (required)  your people_products schema
│   ├── my_load.sql              (required)  the loader you adapted
│   ├── 05_load.md               (required)  build commands + row counts
│   └── 06_queries.md            (required)  pytest output + /docs and /fast check
│
├── duckdb/                      unit 02
│   ├── FINDINGS_duckdb.md       (required)  the template, filled in, plus the "both" scenario
│   ├── 01_why.md                (required)  paragraph + predictions (written before measuring)
│   ├── 03_connect.md            (required)  hello x3 + DESCRIBE vs .schema
│   ├── 04_model.md              (required)  predictions, sizes, compression, Q09 times, B4 calls
│   ├── 05_load.md               (required)  builds, sniffer, Parquet vs. CSV
│   └── 06_queries.md            (required)  translation table, /docs check, one shortcut
│
└── api/                         your copy of the field guide's lab/api/starter_code
    ├── pyproject.toml               copied
    ├── .env.example                 copied
    ├── driver.py                    copied
    ├── app/
    │   ├── __init__.py              copied
    │   ├── main.py              (required)  YOUR routes: Q03, Q08, Q15
    │   ├── experiment.py            copied (SQLite harness)
    │   ├── experiment_duckdb.py     copied (ENGINE=duckdb)
    │   └── models.py                copied
    ├── tests/
    │   ├── conftest.py              copied
    │   ├── test_smoke.py            copied
    │   └── test_your_routes.py      copied: must pass
    ├── results_sqlite/          (required, generated)  full driver run on SQLite
    │   ├── results.csv
    │   └── results.md
    └── results_duckdb/          (required, generated)  full driver run on DuckDB
        ├── results.csv
        └── results.md
```

DuckDB has no `02_install.md` because its 02_install section has no
*Your artifact*. Sections 07–09 have no separate files for either engine:
their artifacts go inside the FINDINGS file, which the course template
already lays out.

Because `api/` lives outside the field guide clone, set `FIELD_GUIDE` so it
can find the SQL files:

```bash
export FIELD_GUIDE="$HOME/5303/5303-Database-Field-Guide/assignments/Performance_Project"
```

## How the files map to the nine sections

| Section | SQLite | DuckDB |
| ------- | ------ | ------ |
| 01 Why it exists | `sqlite/01_why.md` | `duckdb/01_why.md` (predictions are checked in §7) |
| 02 Install & verify | `sqlite/02_install.md` | — |
| 03 Connect three ways | `sqlite/03_connect.md` | `duckdb/03_connect.md` |
| 04 Model the data | `sqlite/04_model.md`, `your_turn_checks.sql`, `my_schema.sql`, `my_load.sql` | `duckdb/04_model.md` |
| 05 Load it | `sqlite/05_load.md` | `duckdb/05_load.md` |
| 06 Query catalog | `api/app/main.py`, `sqlite/06_queries.md` | `duckdb/06_queries.md` |
| 07 Explain & measure | `api/results_sqlite/`, FINDINGS *Results (§7)* | `api/results_duckdb/`, FINDINGS *Results (§7)* |
| 08 Concurrency & load | FINDINGS *Load (§8)* | FINDINGS *Load (§8)* |
| 09 When to choose it | FINDINGS *When to choose it (§9)*: 7 verdicts | FINDINGS §9: 9 verdicts + "both" |

## Your `README.md`

The file you're reading explains the structure. **Your**
`Performance_Project/README.md` is an index, not a report. It holds:

- Your machine (CPU, RAM, disk) and OS, since every number depends on them.
- The `DATA_DIR` (and `DUCKDB_DIR`, if set) you used, so the paths in your
  commands make sense to a reader.
- A link table:

  | Unit   | FINDINGS                     | Driver results                   |
  | ------ | ---------------------------- | -------------------------------- |
  | SQLite | `sqlite/FINDINGS_sqlite.md`  | `api/results_sqlite/results.md`  |
  | DuckDB | `duckdb/FINDINGS_duckdb.md`  | `api/results_duckdb/results.md`  |

## Acceptable variations

**Sections 01–06 in one file.** Instead of one `.md` per section, you may
put the §1–§6 artifacts at the top of the FINDINGS file under headings like
`## §1 Why it exists`, above the template's *Environment* section. Either
works; don't split one section across both.

**File names.**

| Shown | Also fine |
| ----- | --------- |
| `01_why.md` ... `06_queries.md` | `s01_why.md`, `notes_01_why.md`, `why.md`. Keep the section number somewhere |
| `my_load.sql` | `my_loader.sql`, `load_people_products.sql`, or a Python loader (`my_load.py`); a `my_rebuild.sql` that runs schema + load is a nice extra |
| `api/` | `measurement_api/`, `starter_code/`, as long as your `README.md` says where it is |
| `results_sqlite/` | `results/` from the SQLite unit's first run, if you didn't rerun with `--out results_sqlite` in DuckDB §7. Results from a full run must exist for both engines either way |

**Extra files that are welcome.**

- `duckdb/shortcut.sql` (or `q09_shortcut.sql`, ...): the DuckDB shortcut
  query from §6 as its own file, referenced from `06_queries.md`.
- Raw `loadtest.py` output saved as text, e.g. `sqlite/loadtest_runs.txt`.
  The summary table and the exact error text still belong in FINDINGS.
- The optional
  [triggers and procedures](../../assignments/performance_project/engines/01_sqlite/05_load/triggers_and_procedures.md)
  walkthrough's `sql/*.sql` scripts. The walkthrough builds them in a
  git-ignored folder; copy them into `sqlite/sql/` if you want to keep them.
- Screenshots of `/docs` or QueryMux, in a `screenshots/` folder inside the
  unit.

**Later units.** If PostgreSQL and MongoDB are assigned, add `postgres/` and
`mongodb/` with the same pattern (`FINDINGS_postgres.md`, `01_why.md`, ...),
plus `api/results_postgres/` and `api/results_mongodb/`. Postgres §4 adds a
`roles.sql`. Redis and the tracks are still stubs.

## What must NOT be in the folder

The `.gitignore` here covers these, but check `git status` anyway:

- Any `.db`, `.duckdb`, `.duckdb.wal`, `-wal`, or `-shm` file, including
  `writes.db` / `writes.duckdb` from §8. They rebuild from the loaders and
  `make_dbs.py`.
- `*.parquet`, `purchases_1m.csv`, and `export_10k/` from DuckDB §5.
- `.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`.
- A `.env` with real settings (commit `.env.example` instead).

Don't edit files inside the field guide clone either. If you did, `git stash`
there and copy your version into `Performance_Project/`.

## Common mistakes the structure helps you catch

- FINDINGS with answers that cite no number or plan line.
- `results.md` from a `--sizes 10k` quick check instead of a full run.
- `main.py` with the three `TODO`s still there (or `test_your_routes.py`
  edited to pass).
- DuckDB §1 predictions written after the measurements. Commit `01_why.md`
  before you run §7; your commit history shows it.
- Only one engine's `results_*` folder: the DuckDB §7 comparison needs both.

## Check your folder

The field guide's [check_completed.py](../../check_completed.py) compares
your folder with this one and looks inside each file for work of your own.
Run it from your course repo:

```bash
cd ~/5303/my-repo
python ~/5303/5303-Database-Field-Guide/check_completed.py performance
```

✅ means the file is there with content of your own, 🟡 is worth a look,
❌ is missing or still the template, and ⚪ is optional. It checks that your
work is **there**, not that it's **right**.
