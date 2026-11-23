# 00 — Setup

Install once, use all semester. Do these in order; each page ends with a
check that proves it worked.

| # | Page                            | You'll have                                              | Needed by         |
| - | ------------------------------- | -------------------------------------------------------- | ----------------- |
| 1 | [git_github.md](git_github.md)  | The field guide cloned, and a `Performance_Project/` folder in your course repo | everything        |
| 2 | [python.md](python.md)          | Python 3.11+, virtual environments, `pip`, `pipx`        | everything        |
| 3 | [editor.md](editor.md)          | VS Code with the extensions this course uses             | everything        |
| 4 | [querymux.md](querymux.md)      | QueryMux, for querying any engine side by side           | unit 01 onward    |
| 5 | [docker.md](docker.md)          | Docker, for the server engines                           | unit 03 (Postgres) onward |

SQLite needs nothing beyond this page: [01_sqlite/02_install](../engines/01_sqlite/02_install/README.md)
checks it. DuckDB installs in [02_duckdb/02_install](../engines/02_duckdb/02_install/README.md).

## The finished setup

```
~/5303/
├── 5303-Database-Field-Guide/   the course materials (clone it, don't edit it)
└── my-repo/                     your course repo, one folder per assignment
    └── Performance_Project/     this project: FINDINGS, routes, schemas
```

> **Keep both folders out of iCloud Drive, OneDrive, Dropbox, and Google
> Drive.** Sync clients copy files one at a time while a database has them
> open, and they move Git's internal files around in ways Git doesn't expect.
> Your home folder is fine. On macOS, `~/Documents` and `~/Desktop` are
> synced to iCloud on many machines, so avoid those too.
