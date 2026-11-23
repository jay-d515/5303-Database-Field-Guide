# FINDINGS template

Copy the part between the lines below to `FINDINGS_<engine>.md`
(e.g. `FINDINGS_sqlite.md`) in your course repo's `Performance_Project/<engine>/`
folder, one file per unit, and fill it in.

Keep answers short: one to three sentences each. Every answer points at a
**number** from your results or a **plan line**. An answer without one is
an opinion.

---

```markdown
# FINDINGS: <engine>

## Environment

- Engine and version:
- Python version (`python --version`):
- Machine (CPU, RAM, SSD or spinning disk):
- Running in Docker? (yes / no):
- Settings that affect speed or durability (journal mode, synchronous, ...):

## Data

| Size | purchases | customers | products |
| :--- | --------: | --------: | -------: |
| 10k  |           |           |          |
| 100k |           |           |          |
| 1m   |           |           |          |

Indexes in the `idx_*` databases (paste the list):

    (paste here)

## Results (§7)

Paste your whole `results.md`. All times are warm, median milliseconds.

(paste here)

### Plan summaries

The one or two plan lines that explain each query's time, in the largest
databases. Describe how the engine runs it, not what the query does.

| Query | `noidx_1m` plan | `idx_1m` plan |
| :---- | :-------------- | :------------ |
| Q01   |                 |               |
| ...   |                 |               |

### Questions

Answer whatever your unit's `07_explain/` asks for under *Your artifact*.

## Load (§8)

| Run | Scenario | n | settings | succeeded | failed | seconds | succeeded/sec | p95 ms |
| :-- | :------- | -: | :------- | --------: | -----: | ------: | ------------: | -----: |
|     |          |    |          |           |        |         |               |        |

Exact error text from a failed request:

    (paste here)

### Questions

Copy the questions from your unit's `08_concurrency/` here and answer them.

## When to choose it (§9)

For each scenario in your unit's `09_when/`: **yes or no**, one or two
sentences, and one number from above.

1.
2.
3.

## One surprise

What did your numbers show that you didn't expect, and what explains it?
```
