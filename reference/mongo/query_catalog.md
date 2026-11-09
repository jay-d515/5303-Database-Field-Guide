# Query Catalog: MongoDB Solutions (`store` database)

Instructor key for every query in
[datasets/store2/query_catalog.md](../../datasets/store2/query_catalog.md),
rewritten for the **`store`** database (the collections exported in
[datasets/store/](../../datasets/store/)). Syntax is `mongosh`:

```bash
mongosh store
```

Every query below was run against `store` on MongoDB 9.0.4 (2026-11-09).
Timings are from that run. The Q15 transaction was tested on a temporary
one-member replica set, because the local `mongod` is standalone.

## The `store` collections

| Collection       | Docs   | Shape (fields used here)                                                                      |
| ---------------- | ------ | --------------------------------------------------------------------------------------------- |
| `customers`      | 2,000  | `customer_id, first_name, last_name, email, city, state, created_at`                          |
| `orders`         | 8,000  | `order_id, customer_id, status, total_cents, created_at`                                      |
| `order_items`    | 13,491 | `order_id, product_id, quantity, unit_price_cents`                                            |
| `products`       | 5,000  | `product_id, category_id, name, brand, price_cents, stock, description, …`                    |
| `categories`     | 357    | `category_id, parent_id, name, slug`: 15 top-level (`parent_id: ""`) with 342 leaves under them |
| `product_images` | 18,156 | `product_id, sort_order, path, is_main` (not used by the catalog)                             |
| `counters`       | 2      | `{_id: "order_id", seq: 8000}`, `{_id: "customer_id", seq: 2000}`                             |

### How the catalog's vocabulary maps onto `store`

The catalog was written for the `store2` purchases schema. Here is how each of
its terms translates:

| Catalog says   | In `store`                                                                                                     |
| -------------- | -------------------------------------------------------------------------------------------------------------- |
| purchase       | an **order** (Q03, Q04, Q06, Q11, Q12, Q15) or an **order line item** (Q05, Q08, Q10, Q14)                     |
| department     | a **top-level category**. Each product points to a leaf category, and the leaf's `parent_id` is the department |
| state          | `customers.state`: orders don't carry it, so it takes a join                                                   |
| amount/revenue | `orders.total_cents` or `quantity × unit_price_cents`, **integer cents**. Divide by 100 only for display       |
| date           | `created_at`, an **ISO-8601 string** (`"2025-03-01T06:34:34Z"`), not a BSON `Date`                             |
| revenue        | excludes `status: "cancelled"` (313 of 8,000 orders). Other statuses count                                     |

Two consequences worth pointing out to students:

1. **Dates are strings.** Because they're ISO-8601 in UTC, comparing them
   as strings gives the same answer as comparing them as dates, so
   `{created_at: {$gte: "2025-03-01", $lt: "2025-03-08"}}` works, and the month
   is just `{$substrBytes: ["$created_at", 0, 7]}`. Real date arithmetic (Q06)
   needs `$dateFromString` first.
2. **This is a normalized, SQL-shaped design.** Nothing is embedded and
   nothing is copied in. Almost every report needs `$lookup`, and the
   `$lookup` key fields have **no indexes** (only `_id` is indexed, and `_id` is an
   ObjectId the queries never use).

### Indexes

The `store` database ships with `_id` indexes only. Every query works
without the indexes below; the ones that join get much faster with them:

```js
db.customers.createIndex({ customer_id: 1 }, { unique: true });
db.orders.createIndex({ order_id: 1 }, { unique: true });
db.orders.createIndex({ customer_id: 1, created_at: -1 });   // Q04 (ESR: equality, then sort)
db.orders.createIndex({ created_at: 1 });                    // Q03, Q07, Q14
db.order_items.createIndex({ order_id: 1 });
db.order_items.createIndex({ product_id: 1 });
db.products.createIndex({ product_id: 1 }, { unique: true });
db.products.createIndex({ category_id: 1 });
db.categories.createIndex({ category_id: 1 }, { unique: true });
db.categories.createIndex({ parent_id: 1 });
```

Measured (ms, `mongosh`, local):

| Query                  | `_id` only | with indexes | Why                                                           |
| ---------------------- | ---------: | -----------: | ------------------------------------------------------------- |
| Q04 history            |        281 |           31 | `$lookup` into `order_items` per order                        |
| Q05 dept count         |        255 |           18 | three chained `$lookup`s                                      |
| Q08 dead products      |      1,346 |           32 | `$lookup` into `orders` and `order_items`                     |
| Q09 revenue by state   |      1,744 |          102 | one `$lookup` per order (8,000 collection scans of customers) |
| Q09 (group first)      |        393 |           26 | groups to ≤2,000 customers *before* the `$lookup`             |
| **Q10 top products**   | **12,114** |      **169** | 13,491 `$lookup`s, each scanning all 8,000 orders             |
| Q14 cube               |          — |          623 | five `$lookup`s per order line                                |
| build `monthly_cube`   |     21,508 |          774 | same pipeline as Q14 over all of history                      |
| everything else        |        < 8 |          < 4 |                                                               |

For a caching lesson, **Q10 and Q09 without indexes** are the vivid
examples: a 12-second report with a 10-row answer. They also make the point
that **the first fix is an index, not Redis**.

## Summary

| ID  | Intent                            | Fit | MongoDB shape                                                  | Cache candidate?                                    |
| --- | --------------------------------- | :-: | -------------------------------------------------------------- | --------------------------------------------------- |
| Q01 | One customer by id                |  ✓  | `findOne`                                                      | No, already sub-millisecond                         |
| Q02 | One page of products              |  ✓  | `find` + `sort` + `skip`/`limit`                               | Yes, the catalog changes rarely                     |
| Q03 | Orders in a date range            |  ✓  | `find` with string range                                       | Past ranges yes; "today" no                         |
| Q04 | A customer's order history        |  ~  | `find`-like `$match/$sort/$limit` + `$lookup` items & names    | Yes, invalidate on that customer's new order        |
| Q05 | Count purchases in one department |  ~  | walk the category tree down, then count line items             | Yes, or a Redis counter                             |
| Q06 | A customer's purchase streaks     |  ~  | `$dateFromString` + `$setWindowFields` + `$dateSubtract`       | Yes, per customer                                   |
| Q07 | 90-day spending leaderboard       |  ~  | `$group` + `$rank`, `$lookup` names for the top 20 only        | Yes, or a Redis sorted set                          |
| Q08 | Products never bought in a state  |  ~  | customers → orders → items → `$addToSet`, then `$not $in`      | Yes: expensive, slow-changing                       |
| Q09 | Revenue by state                  |  ~  | `$lookup` customer state, `$group`                             | **Best case**: scan + join, 28-row answer           |
| Q10 | Top 10 products by revenue        |  ~  | items `$lookup` order status, `$group`, top 10, `$lookup` name | **Best case**: 12 s unindexed, 10-row answer        |
| Q11 | Deep pagination                   |  ✓  | `skip` vs. `order_id: {$gt: after_id}`                         | No: fix the query (keyset)                          |
| Q12 | Random sample                     |  ✓  | `$sample` vs. random `order_id`s                               | No: a cached sample isn't random                    |
| Q13 | Revenue by month                  |  ✓  | `$group` on `$substrBytes` vs. `monthly_sales`                 | The summary collection *is* a cache                 |
| Q14 | State × department × month report |  ✗~ | five `$lookup`s, one `$group` vs. `monthly_cube`               | Yes, keyed by `start:end:min`                       |
| Q15 | Insert an order                   |  ~  | validate, counter, insert order + items / transaction          | Write path: this is what *invalidates* the caches   |
| Q16 | Search product text (proposed)    |  ✓  | `text` index + `$text`                                         | Popular searches, yes                               |

---

## Q01 — One customer by id

`GET /customers?customer_id=…`

```js
const customer_id = 7;

db.customers.findOne(
  { customer_id: customer_id },
  { _id: 0, customer_id: 1, first_name: 1, last_name: 1, email: 1, city: 1, state: 1 }
);
```

```js
{ customer_id: 7, first_name: 'Peter', last_name: 'Hanson',
  email: 'peter.hanson@example.com', city: 'Columbus', state: 'OH' }
```

Note: `customer_id` is **not** `_id`, so without the unique index this is a
`COLLSCAN` of 2,000 documents, not `IDHACK`. It's still fast at this size.

## Q02 — One page of products

`GET /products?limit=…&offset=…`

```js
const limit = 50, offset = 0;

db.products.find({}, { _id: 0, product_id: 1, name: 1, brand: 1, price_cents: 1 })
  .sort({ product_id: 1 }).skip(offset).limit(limit);
```

Keyset version (the pattern's point), given the last `product_id` of the
previous page:

```js
const after_id = 50;

db.products.find({ product_id: { $gt: after_id } },
                 { _id: 0, product_id: 1, name: 1, brand: 1, price_cents: 1 })
  .sort({ product_id: 1 }).limit(limit);
```

## Q03 — Orders in a date range

`GET /purchases?start=…&end=…` (end exclusive)

```js
const start = "2025-03-01", end = "2025-03-08";

db.orders.find(
  { created_at: { $gte: start, $lt: end } },
  { _id: 0, order_id: 1, customer_id: 1, status: 1, total_cents: 1, created_at: 1 }
).sort({ created_at: 1, order_id: 1 }).limit(100);
```

78 orders in that week. Plain strings work as bounds because ISO-8601
timestamps sort in time order: `"2025-03-07T23:59:59Z" < "2025-03-08"`.

## Q04 — A customer's order history

`GET /customers/purchases?customer_id=…`

```js
const customer_id = 1668;

db.orders.aggregate([
  { $match: { customer_id: customer_id } },
  { $sort: { created_at: -1, order_id: -1 } },
  { $limit: 100 },                                  // limit BEFORE the joins
  { $lookup: {
      from: "order_items", localField: "order_id", foreignField: "order_id", as: "items",
      pipeline: [
        { $lookup: { from: "products", localField: "product_id", foreignField: "product_id",
                     as: "p", pipeline: [{ $project: { _id: 0, name: 1 } }] } },
        { $project: { _id: 0, product_id: 1, product_name: { $first: "$p.name" },
                      quantity: 1, unit_price_cents: 1 } }
      ] } },
  { $project: { _id: 0, order_id: 1, created_at: 1, status: 1, total_cents: 1, items: 1 } }
]);
```

The result is one document per order with its line items nested inside. That
nesting is the document model's advantage, even though the data is stored
normalized. The `$limit` before the `$lookup` matters: only 100 orders get
joined, not all 384 of customer 1668's. With
`{customer_id: 1, created_at: -1}` the match and sort come straight off the
index.

## Q05 — Count purchases in one department

`GET /stats/department_count?department=…`

Department = top-level category. Walk the tree **down**: department → its
leaf categories → their products → line items.

```js
const department = "Electronics";

db.categories.aggregate([
  { $match: { parent_id: "", name: department } },
  { $lookup: { from: "categories", localField: "category_id", foreignField: "parent_id", as: "leaf" } },
  { $unwind: "$leaf" },
  { $lookup: { from: "products", localField: "leaf.category_id", foreignField: "category_id", as: "p",
               pipeline: [{ $project: { _id: 0, product_id: 1 } }] } },
  { $unwind: "$p" },
  { $lookup: { from: "order_items", localField: "p.product_id", foreignField: "product_id", as: "oi",
               pipeline: [{ $project: { _id: 0, order_id: 1, quantity: 1 } }] } },
  { $unwind: "$oi" },
  { $group: { _id: null, num_line_items: { $sum: 1 }, units: { $sum: "$oi.quantity" },
              orders: { $addToSet: "$oi.order_id" } } },
  { $project: { _id: 0, department: department, num_orders: { $size: "$orders" },
                num_line_items: 1, units: 1 } }
]);
```

```js
{ department: 'Electronics', num_orders: 360, num_line_items: 368, units: 529 }
```

The same answer as three small queries, the way an application would often do
it (2 ms, even unindexed):

```js
const deptId     = db.categories.findOne({ parent_id: "", name: department }).category_id;
const leafIds    = db.categories.distinct("category_id", { parent_id: deptId });
const productIds = db.products.distinct("product_id", { category_id: { $in: leafIds } });

db.order_items.aggregate([
  { $match: { product_id: { $in: productIds } } },
  { $group: { _id: null, num_line_items: { $sum: 1 }, units: { $sum: "$quantity" },
              orders: { $addToSet: "$order_id" } } },
  { $project: { _id: 0, num_orders: { $size: "$orders" }, num_line_items: 1, units: 1 } }
]);
```

"Purchases" is ambiguous here. One order can contain several Electronics
items, so 360 orders ≠ 368 line items ≠ 529 units. The query reports all
three. This counts every status. Add `status: {$ne: "cancelled"}` through an
orders `$lookup` if the class definition excludes cancelled orders.

## Q06 — A customer's purchase streaks

`GET /customers/streaks?customer_id=…`

Gaps and islands: number the distinct order days in order. Subtracting the
row number from the date gives the same value for every day in a
consecutive run.

```js
const customer_id = 1668;

db.orders.aggregate([
  { $match: { customer_id: customer_id, status: { $ne: "cancelled" } } },
  { $group: { _id: { $dateFromString: {                       // string -> Date, day only
      dateString: { $substrBytes: ["$created_at", 0, 10] } } } } },
  { $setWindowFields: { sortBy: { _id: 1 },
                        output: { rn: { $documentNumber: {} } } } },   // ROW_NUMBER()
  { $group: {
      _id: { $dateSubtract: { startDate: "$_id", unit: "day", amount: "$rn" } },
      streak_start: { $min: "$_id" }, streak_end: { $max: "$_id" }, days: { $sum: 1 } } },
  { $match: { days: { $gte: 2 } } },
  { $sort: { days: -1, streak_start: 1 } },
  { $limit: 10 },
  { $project: { _id: 0, days: 1,
      streak_start: { $dateToString: { date: "$streak_start", format: "%Y-%m-%d" } },
      streak_end:   { $dateToString: { date: "$streak_end",   format: "%Y-%m-%d" } } } }
]);
```

```js
{ days: 8, streak_start: '2025-02-14', streak_end: '2025-02-21' }
{ days: 7, streak_start: '2024-08-31', streak_end: '2024-09-06' }
...
```

Good demo customers: 759 (567 orders), 1668 (384), 360 (164).

## Q07 — 90-day spending leaderboard

`GET /stats/leaderboard?start=…&end=…` (the data ends 2025-12-30)

```js
const start = "2025-10-01", end = "2025-12-30";

db.orders.aggregate([
  { $match: { created_at: { $gte: start, $lt: end }, status: { $ne: "cancelled" } } },
  { $group: { _id: "$customer_id", total_cents: { $sum: "$total_cents" }, num_orders: { $sum: 1 } } },
  { $setWindowFields: { sortBy: { total_cents: -1 }, output: { rank: { $rank: {} } } } },   // RANK()
  { $sort: { total_cents: -1, _id: 1 } },
  { $limit: 20 },
  { $lookup: { from: "customers", localField: "_id", foreignField: "customer_id", as: "c",
               pipeline: [{ $project: { _id: 0, first_name: 1, last_name: 1, state: 1 } }] } },
  { $unwind: "$c" },
  { $project: { _id: 0, rank: 1, customer_id: "$_id", first_name: "$c.first_name",
                last_name: "$c.last_name", state: "$c.state", num_orders: 1, total_cents: 1 } }
]);
```

```js
{ rank: 1, customer_id: 759,  first_name: 'Scarlette', last_name: 'Sharp', state: 'IL', num_orders: 534, total_cents: 8108240 }
{ rank: 2, customer_id: 1668, first_name: 'Aydin',     last_name: 'Baker', state: 'NC', num_orders: 59,  total_cents: 1438827 }
...
```

The names are joined **after** `$limit: 20`, so only 20 lookups run. That's
why this one is fast even without indexes. `$denseRank` would give
`DENSE_RANK()`. For a live leaderboard, Redis `ZINCRBY leaderboard <cents>
<customer_id>` on every order plus `ZREVRANGE … WITHSCORES` replaces this
query outright. That isn't caching, though: it's moving the computation to
the write side.

## Q08 — Products never bought in a state

`GET /products/dead?state=…`

Anti-join. State lives on customers, so walk customers → orders → items to
get the set of products bought, then keep the products not in it.

```js
const state = "TX";

db.customers.aggregate([
  { $match: { state: state } },
  { $lookup: { from: "orders", localField: "customer_id", foreignField: "customer_id", as: "o",
               pipeline: [{ $match: { status: { $ne: "cancelled" } } }, { $project: { _id: 0, order_id: 1 } }] } },
  { $unwind: "$o" },
  { $lookup: { from: "order_items", localField: "o.order_id", foreignField: "order_id", as: "oi",
               pipeline: [{ $project: { _id: 0, product_id: 1 } }] } },
  { $unwind: "$oi" },
  { $group: { _id: null, bought: { $addToSet: "$oi.product_id" } } },
  { $lookup: { from: "products", let: { bought: "$bought" }, as: "dead",
               pipeline: [
                 { $match: { $expr: { $not: { $in: ["$product_id", "$$bought"] } } } },
                 { $sort: { product_id: 1 } },
                 { $limit: 100 },
                 { $project: { _id: 0, product_id: 1, name: 1 } } ] } },
  { $unwind: "$dead" },
  { $replaceWith: "$dead" }
]);
```

Step-by-step version (same 100 rows, 2–3 ms):

```js
const custIds  = db.customers.distinct("customer_id", { state: state });
const orderIds = db.orders.distinct("order_id", { customer_id: { $in: custIds }, status: { $ne: "cancelled" } });
const bought   = db.order_items.distinct("product_id", { order_id: { $in: orderIds } });

db.products.find({ product_id: { $nin: bought } }, { _id: 0, product_id: 1, name: 1 })
  .sort({ product_id: 1 }).limit(100);
```

4,163 of 5,000 products have never been bought in Texas: most of the catalog
is "dead" because there are only 13,491 line items. One edge case in the
pipeline version: if a state has no orders at all, the `$group` emits nothing
and the query returns 0 rows instead of every product. The step version
doesn't have that bug.

## Q09 — Revenue by state

`GET /stats/revenue_by_state`

```js
db.orders.aggregate([
  { $match: { status: { $ne: "cancelled" } } },
  { $lookup: { from: "customers", localField: "customer_id", foreignField: "customer_id", as: "c",
               pipeline: [{ $project: { _id: 0, state: 1 } }] } },
  { $group: { _id: { $first: "$c.state" }, num_orders: { $sum: 1 }, revenue_cents: { $sum: "$total_cents" } } },
  { $sort: { revenue_cents: -1, _id: 1 } },
  { $project: { _id: 0, state: "$_id", num_orders: 1, revenue_cents: 1 } }
]);
```

Better: **group first, join second**. 7,687 orders collapse to ≤2,000
customers before the `$lookup`. Same rows, 4× faster in both index variants:

```js
db.orders.aggregate([
  { $match: { status: { $ne: "cancelled" } } },
  { $group: { _id: "$customer_id", n: { $sum: 1 }, r: { $sum: "$total_cents" } } },
  { $lookup: { from: "customers", localField: "_id", foreignField: "customer_id", as: "c",
               pipeline: [{ $project: { _id: 0, state: 1 } }] } },
  { $group: { _id: { $first: "$c.state" }, num_orders: { $sum: "$n" }, revenue_cents: { $sum: "$r" } } },
  { $sort: { revenue_cents: -1, _id: 1 } },
  { $project: { _id: 0, state: "$_id", num_orders: 1, revenue_cents: 1 } }
]);
```

```js
{ state: 'TX', num_orders: 788, revenue_cents: 14025508 }
{ state: 'IL', num_orders: 652, revenue_cents: 10362883 }
...            // 28 states
```

## Q10 — Top 10 products by revenue

`GET /products/top`

```js
db.order_items.aggregate([
  { $lookup: { from: "orders", localField: "order_id", foreignField: "order_id", as: "o",
               pipeline: [{ $project: { _id: 0, status: 1 } }] } },
  { $match: { "o.status": { $ne: "cancelled" } } },
  { $group: { _id: "$product_id", units: { $sum: "$quantity" },
              revenue_cents: { $sum: { $multiply: ["$quantity", "$unit_price_cents"] } } } },
  { $sort: { revenue_cents: -1, _id: 1 } },
  { $limit: 10 },
  { $lookup: { from: "products", localField: "_id", foreignField: "product_id", as: "p",
               pipeline: [{ $project: { _id: 0, name: 1 } }] } },
  { $project: { _id: 0, product_id: "$_id", name: { $first: "$p.name" }, units: 1, revenue_cents: 1 } }
]);
```

```js
{ product_id: 2756, name: 'Amazon Brand – Rivet Thomas Modern Leather Sofa Couch, 101.2", Caramel', units: 90, revenue_cents: 4589910 }
{ product_id: 3010, name: 'Amazon Brand – Ravenna Home Westcott Tufted Loveseat Sofa Couch, 60"W, Grey Velvet', units: 35, revenue_cents: 2589965 }
...
```

Revenue uses the line item's `unit_price_cents` (price **at purchase**), not
the product's current `price_cents`. The status `$lookup` is the expensive
part: **12.1 s unindexed** (13,491 lookups × a scan of 8,000 orders), 169 ms with
`orders.order_id` indexed. Product names are joined only for the final 10.

## Q11 — Deep pagination: skip vs. keyset

`GET /purchases/page?offset=…`

```js
const offset = 7000;

db.orders.find({}, { _id: 0, order_id: 1, customer_id: 1, status: 1, total_cents: 1, created_at: 1 })
  .sort({ order_id: 1 }).skip(offset).limit(50);
```

`GET /purchases/page/fast?after_id=…`

```js
const after_id = 7000;

db.orders.find({ order_id: { $gt: after_id } },
               { _id: 0, order_id: 1, customer_id: 1, status: 1, total_cents: 1, created_at: 1 })
  .sort({ order_id: 1 }).limit(50);
```

Same 50 rows (7001–7050). With the `order_id` index, `skip` still walks 7,050
keys while keyset seeks straight to 7001. With only 8,000 orders, both take
about 2 ms here. The difference only shows at 1m-row scale (see the
`idx_1m` numbers in the MongoDB unit's key). Without the `order_id` index,
**both** sort all 8,000 documents in memory.

## Q12 — Random sample

`GET /purchases/sample`

```js
db.orders.aggregate([
  { $sample: { size: 10 } },
  { $project: { _id: 0, order_id: 1, customer_id: 1, status: 1, total_cents: 1, created_at: 1 } }
]);
```

`GET /purchases/sample/fast`: pick random ids in the application, using the
counter as the upper bound:

```js
const maxId = db.counters.findOne({ _id: "order_id" }).seq;
const ids = Array.from({ length: 10 }, () => 1 + Math.floor(Math.random() * maxId));

db.orders.find({ order_id: { $in: ids } },
               { _id: 0, order_id: 1, customer_id: 1, status: 1, total_cents: 1, created_at: 1 })
  .sort({ order_id: 1 });
```

Fair only while `order_id`s are dense (1..8000, no deletes). It can return
fewer than 10 if two random ids collide.

## Q13 — Revenue by month: scan vs. summary

`GET /stats/revenue_by_month`

```js
db.orders.aggregate([
  { $match: { status: { $ne: "cancelled" } } },
  { $group: { _id: { $substrBytes: ["$created_at", 0, 7] },     // "2025-03"
              num_orders: { $sum: 1 }, revenue_cents: { $sum: "$total_cents" } } },
  { $sort: { _id: 1 } },
  { $project: { _id: 0, month: "$_id", num_orders: 1, revenue_cents: 1 } }
]);
```

18 months (2024-07 … 2025-12). Single collection, no join, so it's < 1 ms even
unindexed at this size.

`GET /stats/revenue_by_month/fast` reads a summary collection. `store` doesn't
have one, so build it first (a materialized view with `$merge`; rerun it to
refresh):

```js
db.monthly_sales.createIndex({ month: 1 }, { unique: true });   // $merge "on" needs a unique index

db.orders.aggregate([
  { $match: { status: { $ne: "cancelled" } } },
  { $group: { _id: { $substrBytes: ["$created_at", 0, 7] },
              num_orders: { $sum: 1 }, revenue_cents: { $sum: "$total_cents" } } },
  { $project: { _id: 0, month: "$_id", num_orders: 1, revenue_cents: 1 } },
  { $merge: { into: "monthly_sales", on: "month", whenMatched: "replace", whenNotMatched: "insert" } }
]);

// Q13 fast
db.monthly_sales.find({}, { _id: 0, month: 1, num_orders: 1, revenue_cents: 1 }).sort({ month: 1 });
```

The teaching point for the Redis unit: `monthly_sales` **is a cache**. It
lives inside the database, it goes stale exactly like a Redis key, and
"when do I rerun the `$merge`?" is the same question as "what's the TTL?"

## Q14 — State × department × month report

`GET /reports/cube?start=…&end=…&min_purchases=…`

Every dimension lives in a different collection: state on customers,
department two levels up the category tree, revenue on line items. So this is
five `$lookup`s per line. In MongoDB it's the least natural query in the
catalog (✗~): SQL's joins plus `GROUP BY` handle it more naturally.

```js
const start = "2025-01-01", end = "2026-01-01", min_purchases = 10;   // min line items per cell

db.orders.aggregate([
  { $match: { created_at: { $gte: start, $lt: end }, status: { $ne: "cancelled" } } },
  { $lookup: { from: "customers", localField: "customer_id", foreignField: "customer_id", as: "c",
               pipeline: [{ $project: { _id: 0, state: 1 } }] } },
  { $lookup: { from: "order_items", localField: "order_id", foreignField: "order_id", as: "item" } },
  { $unwind: "$item" },
  { $lookup: { from: "products", localField: "item.product_id", foreignField: "product_id", as: "p",
               pipeline: [{ $project: { _id: 0, category_id: 1 } }] } },
  { $lookup: { from: "categories", localField: "p.category_id", foreignField: "category_id", as: "leaf",
               pipeline: [{ $project: { _id: 0, parent_id: 1 } }] } },
  { $lookup: { from: "categories", localField: "leaf.parent_id", foreignField: "category_id", as: "dept",
               pipeline: [{ $project: { _id: 0, name: 1 } }] } },
  { $group: {
      _id: { state: { $first: "$c.state" },
             department: { $first: "$dept.name" },
             month: { $substrBytes: ["$created_at", 0, 7] } },
      num_items: { $sum: 1 },
      revenue_cents: { $sum: { $multiply: ["$item.quantity", "$item.unit_price_cents"] } } } },
  { $match: { num_items: { $gte: min_purchases } } },                                  // HAVING
  { $sort: { revenue_cents: -1, "_id.state": 1, "_id.department": 1, "_id.month": 1 } },
  { $limit: 50 },
  { $project: { _id: 0, state: "$_id.state", department: "$_id.department", month: "$_id.month",
                num_items: 1, revenue_cents: 1 } }
]);
```

`GET /reports/cube/fast` uses a summary at exactly the report's grain. It's
built the same way, minus the date filter and `HAVING`:

```js
db.monthly_cube.createIndex({ state: 1, department: 1, month: 1 }, { unique: true });

db.orders.aggregate([
  { $match: { status: { $ne: "cancelled" } } },
  /* ... the same five $lookup / $unwind stages as above ... */
  { $group: {
      _id: { state: { $first: "$c.state" }, department: { $first: "$dept.name" },
             month: { $substrBytes: ["$created_at", 0, 7] } },
      num_items: { $sum: 1 },
      revenue_cents: { $sum: { $multiply: ["$item.quantity", "$item.unit_price_cents"] } } } },
  { $project: { _id: 0, state: "$_id.state", department: "$_id.department", month: "$_id.month",
                num_items: 1, revenue_cents: 1 } },
  { $merge: { into: "monthly_cube", on: ["state", "department", "month"],
              whenMatched: "replace", whenNotMatched: "insert" } }
]);

// Q14 fast: HAVING becomes a plain filter, because the cells are already grouped
db.monthly_cube.find(
  { month: { $gte: start.slice(0, 7), $lt: end.slice(0, 7) }, num_items: { $gte: min_purchases } },
  { _id: 0, state: 1, department: 1, month: 1, num_items: 1, revenue_cents: 1 }
).sort({ revenue_cents: -1, state: 1, department: 1, month: 1 }).limit(50);
```

Verified: the fast version returns exactly the same 50 rows. `monthly_cube`
has 3,894 cells. Building it took 21.5 s unindexed vs. 0.77 s indexed. The
report then takes < 1 ms vs. 623 ms for the live query.

## Q15 — Insert an order

`POST /purchases` with a JSON body. No foreign keys and no auto-increment,
so the application does both jobs: check the references, then take an id
from the counter.

```js
const body = { customer_id: 7, items: [ { product_id: 227, quantity: 2 },
                                         { product_id: 3037, quantity: 1 } ] };

// 1. validate references (MongoDB won't)
const cust = db.customers.findOne({ customer_id: body.customer_id }, { _id: 0, customer_id: 1 });
if (!cust) throw new Error(`no customer ${body.customer_id}`);

const ids = body.items.map(i => i.product_id);
const prices = new Map(
  db.products.find({ product_id: { $in: ids } }, { _id: 0, product_id: 1, price_cents: 1 })
    .toArray().map(p => [p.product_id, p.price_cents]));
const missing = ids.filter(id => !prices.has(id));
if (missing.length) throw new Error(`no product(s) ${missing}`);

// 2. next order id: every writer increments this ONE document
const order_id = db.counters.findOneAndUpdate(
  { _id: "order_id" }, { $inc: { seq: 1 } }, { returnDocument: "after" }).seq;

// 3. write the order and its line items (price copied in at purchase time)
const items = body.items.map(i => ({ order_id, product_id: i.product_id, quantity: i.quantity,
                                     unit_price_cents: prices.get(i.product_id) }));
db.orders.insertOne({
  order_id, customer_id: body.customer_id, status: "pending",
  total_cents: items.reduce((s, i) => s + i.quantity * i.unit_price_cents, 0),
  created_at: new Date().toISOString().replace(/\.\d{3}Z$/, "Z")      // match the stored string format
});
db.order_items.insertMany(items);
```

Tested: creates order 8001 (`total_cents: 47997`) with two line items. A
missing customer or product is rejected **before** the counter moves, so no
ids are wasted. The gap this leaves open: steps 2 and 3 aren't atomic. A
crash between the order and its items leaves an order with no lines. That's
what `/fast` fixes.

`POST /purchases/fast` with a JSON array: all orders and their items in
**one multi-document transaction**.

> **Requires a replica set.** The local `mongod` that holds `store` is
> standalone (`rs.status()` → "not running with --replSet"), so this fails
> there with *Transaction numbers are only allowed on a replica set member or mongos*.
> The course Docker image (`mongo:9`, one-member replica set) runs it as is.

```js
const bodies = [
  { customer_id: 1, items: [ { product_id: 2, quantity: 1 } ] },
  { customer_id: 2, items: [ { product_id: 3, quantity: 1 }, { product_id: 4, quantity: 3 } ] }
];

const session = db.getMongo().startSession();
const sdb = session.getDatabase("store");
session.startTransaction({ readConcern: { level: "snapshot" }, writeConcern: { w: "majority" } });
try {
  const custIds = [...new Set(bodies.map(b => b.customer_id))];
  if (sdb.customers.countDocuments({ customer_id: { $in: custIds } }) !== custIds.length)
    throw new Error("unknown customer in batch");

  const ids = [...new Set(bodies.flatMap(b => b.items.map(i => i.product_id)))];
  const prices = new Map(sdb.products.find({ product_id: { $in: ids } }, { _id: 0, product_id: 1, price_cents: 1 })
    .toArray().map(p => [p.product_id, p.price_cents]));
  if (prices.size !== ids.length) throw new Error("unknown product in batch");

  // reserve a block of ids with ONE counter update for the whole batch
  const last = sdb.counters.findOneAndUpdate(
    { _id: "order_id" }, { $inc: { seq: bodies.length } }, { returnDocument: "after" }).seq;
  let next = last - bodies.length + 1;

  const now = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  const orders = [], items = [];
  for (const b of bodies) {
    const order_id = next++;
    const its = b.items.map(i => ({ order_id, product_id: i.product_id, quantity: i.quantity,
                                    unit_price_cents: prices.get(i.product_id) }));
    items.push(...its);
    orders.push({ order_id, customer_id: b.customer_id, status: "pending", created_at: now,
                  total_cents: its.reduce((s, i) => s + i.quantity * i.unit_price_cents, 0) });
  }
  sdb.orders.insertMany(orders);
  sdb.order_items.insertMany(items);
  session.commitTransaction();
} catch (e) {
  session.abortTransaction();
  throw e;
} finally {
  session.endSession();
}
```

Tested on a temporary one-member replica set: a good batch committed orders
8002–8003 and three line items. A batch containing an unknown product wrote
nothing and left the counter unchanged. (Use explicit
`startTransaction`/`commitTransaction` in `mongosh` scripts, as above.
`session.withTransaction(fn)` isn't awaited inside a `try/finally`, so the
session ends before the transaction runs: *Use of expired sessions is not
permitted*.)

Concurrency point: every transaction writes the same `counters` document, so
concurrent batches hit `WriteConflict` (retried as
`TransientTransactionError`). Reserving a block with `$inc: bodies.length`
means one conflict point per batch rather than one per order.

**For the caching unit:** a new order makes these cached answers stale:
Q04 (that customer), Q05 (those departments), Q06, Q07, Q09 (that state), Q10,
Q13, and Q14 (and the `monthly_*` summaries). Deleting those keys on write is
the invalidation half of cache-aside. Notice how many there are for one
insert.

---

## Q16 (proposed) — Search product text

The catalog proposes full-text search over review text. `store` has no
`reviews` collection, but `products` already has `name` and `description`, so
search those:

```js
db.products.createIndex(
  { name: "text", description: "text" },
  { weights: { name: 5, description: 1 }, name: "products_text" });   // one text index per collection

const q = "leather sofa";

db.products.find(
  { $text: { $search: q } },
  { _id: 0, product_id: 1, name: 1, price_cents: 1, score: { $meta: "textScore" } }
).sort({ score: { $meta: "textScore" } }).limit(5);
```

```js
{ product_id: 1940, name: 'Amazon Brand – Stone & Beam Brandeberry Leather Sofa, 82"W, Saddle', price_cents: 160999, score: 7.17 }
{ product_id: 2756, name: 'Amazon Brand – Rivet Thomas Modern Leather Sofa Couch, 101.2", Caramel', price_cents: 50999, score: 6.99 }
...
```

5 ms. `"leather sofa"` without inner quotes matches documents with *either*
word, ranked. `"\"leather sofa\""` is the exact phrase (12 matches). Atlas
Search (`$search`) adds fuzzy matching and highlighting, but needs Atlas or
`mongot`, not community `mongod`.
