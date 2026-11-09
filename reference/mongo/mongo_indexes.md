# MongoDB Indexes

## How to create one

```js
db.orders.createIndex({ customer_id: 1 })                       // single field, ascending
db.orders.createIndex({ customer_id: 1, created_at: -1 })       // compound: field order matters
db.customers.createIndex({ customer_id: 1 }, { unique: true })  // also enforces uniqueness
db.products.createIndex({ name: "text", description: "text" })  // full-text (Q16)

db.orders.getIndexes()                    // list them
db.orders.dropIndex("customer_id_1")      // drop by name
db.orders.hideIndex("customer_id_1")      // planner ignores it, but it's still maintained
db.orders.unhideIndex("customer_id_1")
```

Hiding an index lets you test dropping it safely. If nothing slows down, drop it; if something does, unhide it and it's back instantly, with no rebuild.

## When to create one

The trigger is always the same: `explain("executionStats")` shows far more documents examined than returned, or an in-memory `SORT` stage. Five cases from `store`:

### 1. Equality lookups on a field that isn't `_id`

`store` uses `customer_id`, `order_id` and `product_id` as its real keys, but only `_id` (an ObjectId) is indexed.

```js
db.customers.find({ customer_id: 7 })
```
|                             | Plan             | Keys |  Docs | Returned |
| --------------------------- | ---------------- | ---: | ----: | -------: |
| before                      | `COLLSCAN`       |    0 | 2,000 |        1 |
| `{customer_id: 1}` (unique) | `EXPRESS_IXSCAN` |    1 |     1 |        1 |

### 2. Equality plus a sort: the ESR rule

Q04 asks for a customer's newest orders:
```js
db.orders.find({ customer_id: 1668 }).sort({ created_at: -1 }).limit(10)
```
| Index                              | Plan                     |   Keys |   Docs |
| ---------------------------------- | ------------------------ | -----: | -----: |
| none                               | `SORT ← COLLSCAN`        |      0 |  8,000 |
| `{customer_id: 1}`                 | `SORT ← FETCH ← IXSCAN`  |    384 |    384 |
| `{customer_id: 1, created_at: -1}` | `LIMIT ← FETCH ← IXSCAN` | **10** | **10** |

The single-field index found the customer but still fetched all 384 orders and sorted them in memory. The compound index stores each customer's orders already in date order, so the query reads 10 index entries and stops. That's the **ESR rule** for compound key order: **E**quality fields first, then **S**ort fields, then **R**ange fields.

The compound index also makes `{customer_id: 1}` redundant, because any leading prefix of a compound index works as an index on its own. Drop the single-field one.

### 3. Equality plus a range: field order matters

```js
db.orders.find({ status: "delivered", created_at: { $gte: "2025-03-01", $lt: "2025-04-01" } })
```
| Index                                         |    Keys | Returned |
| --------------------------------------------- | ------: | -------: |
| `{created_at: 1, status: 1}` (range first)    |     369 |      352 |
| `{status: 1, created_at: 1}` (equality first) | **352** |      352 |

With the range field first, MongoDB walks every March order and skips the non-delivered ones. With equality first, it jumps straight to the delivered orders and walks only March. The gap is small here because 90% of orders are delivered; on a rarer status the gap grows.

### 4. `$lookup` join keys

This was the biggest effect. I also found something that changes what I told you earlier.

Q10 (top products) as I wrote it in your catalog:
```js
{ $lookup: { from: "orders", localField: "order_id", foreignField: "order_id", as: "o",
             pipeline: [{ $project: { _id: 0, status: 1 } }] } }
```

| `$lookup` form                                     |                                    No index |    `orders {order_id: 1}` |
| -------------------------------------------------- | ------------------------------------------: | ------------------------: |
| with the `pipeline: [...]` sub-pipeline            | **12,094 ms** (classic engine, nested loop) |                    202 ms |
| plain `localField`/`foreignField`, no sub-pipeline |                      **20 ms** (`HashJoin`) | 31 ms (`IndexedLoopJoin`) |

All four versions return the same answer.

- **Index the field in the *foreign* collection that `foreignField` names.** The index goes on `orders.order_id`, not on `order_items`. With the sub-pipeline form, that index took the query from 12 s to 0.2 s.
- **Correction to my earlier answers:** the 12 seconds came mostly from how I wrote the `$lookup`, not only from the missing index. Adding even a small `pipeline: [{$project}]` makes MongoDB 9 fall back to the old nested-loop `$lookup`. The plain form runs as a hash join and is fast even with no index. You'll see `EQ_LOOKUP` with `"strategy": "HashJoin"` or `"IndexedLoopJoin"` in the explain output only for the plain form. Earlier I called the no-index case `NestedLoopJoin`; in practice the slow version shows no strategy at all.

  Several queries in [query_catalog.md](.profzone/redis_caching/query_catalog.md) use that sub-pipeline form (Q04, Q05, Q08, Q09, Q10, Q14), so its "12 s unindexed" framing is misleading. I can rewrite those queries in the plain form and re-measure.

### 5. Covered queries

If every field the query filters on and returns is inside the index, MongoDB never reads the documents at all:
```js
db.orders.find({ customer_id: 1668 }, { _id: 0, customer_id: 1, created_at: 1 }).sort({ created_at: -1 })
// PROJECTION_COVERED ← IXSCAN: keys 384, docs 0
```
You must exclude `_id` (`_id: 0`), or the query has to fetch each document to get it.

## When *not* to create one

- **The filter matches most of the collection.** `{status: {$ne: "cancelled"}}` matches 96% of orders. The planner did use the status index, but it still read 7,688 index keys and 7,687 documents. That's a full scan plus the index on top; an index only pays off when it narrows the search.
- **Nothing queries that field.** Every index costs disk space and memory, and slows every insert, update and delete on the collection. The `orders` indexes here ranged from 86 KB to 225 KB each, next to 94 KB for `_id`. Write overhead was negligible at this size (20,000 inserts took 87 ms with no extra indexes and 89 ms with four); it shows up at millions of documents or on write-heavy collections.
- **It's a leading prefix of another index.** `{customer_id: 1}` is covered by `{customer_id: 1, created_at: -1}`.
- **The collection is tiny.** `categories` has 357 documents, so a scan costs about the same as an index probe. I'd still give its `category_id` key an index for uniqueness.

**Finding unused indexes:** `db.orders.aggregate([{ $indexStats: {} }])` reports how many times each index has been used since the server started. Only real queries count: in my run the two indexes I'd exercised only through `explain()` showed 0 uses, while `order_id_1` showed 26,982 from the Q10 joins. Look at it after a realistic workload, hide anything still at 0, and drop it if nothing slows down.

## A recommended set for `store`

Based on the catalog queries:

```js
use store
db.customers.createIndex({ customer_id: 1 }, { unique: true });   // Q01, joins from orders
db.customers.createIndex({ state: 1 });                             // Q08
db.orders.createIndex({ order_id: 1 }, { unique: true });          // Q11, joins from order_items
db.orders.createIndex({ customer_id: 1, created_at: -1 });         // Q04, Q06 (ESR)
db.orders.createIndex({ created_at: 1 });                          // Q03, Q07, Q13, Q14 range scans
db.order_items.createIndex({ order_id: 1 });                       // join from orders (Q04, Q14)
db.order_items.createIndex({ product_id: 1 });                     // Q05, Q08
db.products.createIndex({ product_id: 1 }, { unique: true });
db.products.createIndex({ category_id: 1 });                       // Q05 category walk
db.categories.createIndex({ category_id: 1 }, { unique: true });
db.categories.createIndex({ parent_id: 1 });
```

I didn't create these on your real `store`, in case you want students to see the unindexed plans first. Each build takes well under a second at this size. On a large collection, `createIndex` builds while reads and writes continue, and locks the collection only briefly at the start and end.