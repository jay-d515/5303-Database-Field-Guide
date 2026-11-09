#!/usr/bin/env python3
"""
Generate seeded, skewed orders for the people_products dataset.

    python3 generate_orders.py                  # classroom size
    python3 generate_orders.py --size 100k
    python3 generate_orders.py --size 1m --seed 42

Reads  people.csv and products.csv (next to this script)
Writes generated/<size>/orders.csv and order_items.csv

    orders       order_id, person_id, order_date, card_last4
    order_items  order_id, line_no, product_id, quantity, unit_price

Same seed + same size -> byte-identical files.

What makes it look like real commerce rather than uniform noise:
  * A few customers buy a lot; most buy a little (Zipf-like weights).
  * A few products sell a lot; most rarely sell (Zipf-like weights).
  * November and December are busier; weekends a bit busier; daytime hours.
  * An order has 1-5 lines, usually 1; quantity is usually 1.
  * No order is dated after the customer's card expired.
  * ~10% of products changed price once during the history. Lines before the
    change carry the old price, so order_items.unit_price is a real snapshot,
    not a copy of products.price.
  * Orders only store the card's last 4 digits, as real systems do.
"""

import argparse
import bisect
import csv
import random
from datetime import date, datetime, timedelta
from itertools import accumulate
from pathlib import Path

HERE = Path(__file__).parent
SOURCE = HERE
OUT_ROOT = HERE / "generated"

SIZES = {"classroom": 5_000, "10k": 10_000, "100k": 100_000, "1m": 1_000_000}
START = date(2024, 1, 1)
END = date(2026, 8, 31)  # last day of order history

CUSTOMER_SKEW = 0.5  # higher = a few customers dominate more
PRODUCT_SKEW = 0.6
PRICE_CHANGE_SHARE = 0.10

LINES_PER_ORDER = ([1, 2, 3, 4, 5], [50, 25, 13, 8, 4])
QUANTITY = ([1, 2, 3, 4], [80, 12, 5, 3])
MONTH_WEIGHT = {11: 1.5, 12: 1.8}
WEEKEND_WEIGHT = 1.2
HOUR_WEIGHTS = [1, 1, 1, 1, 1, 2, 3, 5, 7, 8, 9, 10, 11, 10, 9, 9, 10, 11, 12, 13, 12, 9, 5, 2]


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def zipf_cum_weights(n, skew, rng):
    """Cumulative Zipf weights over a shuffled order, so popularity isn't tied to id."""
    ranks = list(range(1, n + 1))
    rng.shuffle(ranks)
    return list(accumulate(1 / r**skew for r in ranks))


def pick(rng, cum_weights):
    return bisect.bisect(cum_weights, rng.random() * cum_weights[-1])


def build_days():
    days, weights = [], []
    d = START
    while d <= END:
        w = MONTH_WEIGHT.get(d.month, 1.0) * (WEEKEND_WEIGHT if d.weekday() >= 5 else 1.0)
        days.append(d)
        weights.append(w)
        d += timedelta(days=1)
    return days, list(accumulate(weights))


def price_history(products, rng):
    """For ~10% of products: (change_date, old_price). Before change_date, old_price applied."""
    span = (END - START).days
    history = {}
    for p in products:
        if rng.random() < PRICE_CHANGE_SHARE:
            change = START + timedelta(days=rng.randrange(30, span - 30))
            old = round(float(p["price"]) * rng.uniform(0.80, 0.95), 1) - 0.01
            history[p["id"]] = (change, f"{max(old, 0.49):.2f}")
    return history


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--size", choices=SIZES, default="classroom", help="number of orders (default: classroom)")
    ap.add_argument("--seed", type=int, default=5303, help="random seed (default: 5303)")
    ap.add_argument("--out", type=Path, help="output folder (default: generated/<size>)")
    args = ap.parse_args()

    rng = random.Random(args.seed)
    people = read_csv(SOURCE / "people.csv")
    products = read_csv(SOURCE / "products.csv")

    customer_cw = zipf_cum_weights(len(people), CUSTOMER_SKEW, rng)
    product_cw = zipf_cum_weights(len(products), PRODUCT_SKEW, rng)
    days, day_cw = build_days()
    hour_cw = list(accumulate(HOUR_WEIGHTS))
    lines_cw = list(accumulate(LINES_PER_ORDER[1]))
    qty_cw = list(accumulate(QUANTITY[1]))
    history = price_history(products, rng)

    # Last day each customer can order: the day before their card expired, or END.
    last_day = [
        min(END, datetime.strptime(p["expiration_date"], "%Y-%m-%d %H:%M:%S").date() - timedelta(days=1))
        for p in people
    ]

    orders = []
    for _ in range(SIZES[args.size]):
        c = pick(rng, customer_cw)
        while True:  # resample the date until it's before the card expired
            d = days[pick(rng, day_cw)]
            if d <= last_day[c]:
                break
        ts = datetime(d.year, d.month, d.day, pick(rng, hour_cw), rng.randrange(60), rng.randrange(60))

        n_lines = LINES_PER_ORDER[0][pick(rng, lines_cw)]
        chosen = []
        while len(chosen) < n_lines:
            i = pick(rng, product_cw)
            if i not in chosen:
                chosen.append(i)
        items = []
        for i in chosen:
            prod = products[i]
            price = prod["price"]
            change = history.get(prod["id"])
            if change and d < change[0]:
                price = change[1]
            items.append((prod["id"], QUANTITY[0][pick(rng, qty_cw)], price))
        orders.append((ts, people[c]["id"], people[c]["credit_card"][-4:], items))

    orders.sort(key=lambda o: o[0])  # order ids increase with time, as in a live system

    out = args.out or OUT_ROOT / args.size
    out.mkdir(parents=True, exist_ok=True)
    n_items = 0
    with open(out / "orders.csv", "w", newline="", encoding="utf-8") as fo, \
         open(out / "order_items.csv", "w", newline="", encoding="utf-8") as fi:
        wo = csv.writer(fo, lineterminator="\n")
        wi = csv.writer(fi, lineterminator="\n")
        wo.writerow(["order_id", "person_id", "order_date", "card_last4"])
        wi.writerow(["order_id", "line_no", "product_id", "quantity", "unit_price"])
        for order_id, (ts, person_id, last4, items) in enumerate(orders, start=1):
            wo.writerow([order_id, person_id, ts.strftime("%Y-%m-%d %H:%M:%S"), last4])
            for line_no, (product_id, qty, price) in enumerate(items, start=1):
                wi.writerow([order_id, line_no, product_id, qty, price])
                n_items += 1

    print(f"{args.size}: {len(orders):,} orders, {n_items:,} items -> {out}")


if __name__ == "__main__":
    main()
