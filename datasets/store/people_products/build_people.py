#!/usr/bin/env python3
"""
Build people.csv from the raw people_1..3.csv files.

    python3 build_people.py

Steps (deterministic, safe to re-run):
  1. Combine people_1..3.csv and renumber ids 1..3000.
  2. Check each person's zip against us_zips.csv. A zip that isn't in the
     lookup, or is in a different state, is replaced with a real zip from
     the person's state.
  3. Reset card expiration dates: ~90% still valid through VALID_THROUGH,
     ~10% expired during the order history window.

The raw people_N.csv files and us_zips.csv are never modified.

Zips are read as text throughout. Tools that guess types (Excel, the sqlite3
CLI's .import) turn 01114 into 1114, so don't trust a zip column they've touched.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).parent
SEED = 5303
RAW_FILES = [HERE / f"people_{n}.csv" for n in (1, 2, 3)]
ZIPS = HERE / "us_zips.csv"
OUT = HERE / "people.csv"

VALID_SHARE = 0.90
VALID_THROUGH = datetime(2027, 5, 31)  # end of the academic year
VALID_RANGE = (datetime(2027, 6, 1), datetime(2031, 12, 31))
EXPIRED_RANGE = (datetime(2025, 1, 1), datetime(2026, 7, 31))  # inside order history


def pad_zip(z):
    return z.strip().zfill(5)


def random_datetime(rng, start, end):
    seconds = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randrange(seconds))


def load_lookup():
    """Return {zip: state_abbr} and {state_abbr: [zips]} from us_zips.csv."""
    with open(ZIPS, newline="", encoding="utf-8") as f:
        zip_state = {pad_zip(r["zip"]): r["state_abbr"] for r in csv.DictReader(f)}
    by_state = {}
    for z, st in sorted(zip_state.items()):
        by_state.setdefault(st, []).append(z)
    return zip_state, by_state


def main():
    zip_state, by_state = load_lookup()

    people = []
    for path in RAW_FILES:
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames
            people.extend(reader)

    replaced = expired = 0
    for new_id, p in enumerate(people, start=1):
        p["id"] = str(new_id)
        rng = random.Random(f"{SEED}:{new_id}")  # per-person, so re-runs match

        z = pad_zip(p["zip"])
        if zip_state.get(z) != p["state"]:
            z = rng.choice(by_state[p["state"]])
            replaced += 1
        p["zip"] = z

        if rng.random() < VALID_SHARE:
            exp = random_datetime(rng, *VALID_RANGE)
        else:
            exp = random_datetime(rng, *EXPIRED_RANGE)
            expired += 1
        p["expiration_date"] = exp.strftime("%Y-%m-%d %H:%M:%S")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(people)

    n = len(people)
    print(f"people.csv: {n} rows")
    print(f"  zips replaced (not in lookup): {replaced}")
    print(f"  cards valid through {VALID_THROUGH:%Y-%m-%d}: {n - expired} ({(n - expired) / n:.0%})")


if __name__ == "__main__":
    main()
