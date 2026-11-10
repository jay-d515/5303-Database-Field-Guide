# `store` Schema

```
states ─< zipcodes ─< customers ─< cards ─< purchases >─ products
                                    │                 │
                          card_types┘       departments┘
```

## Candidate extra tables (pick 2–3)

| Table                             | Enables                                            |
| --------------------------------- | -------------------------------------------------- |
| `inventory`                       | Hot-row load scenario                              |
| `reviews`                         | Full-text search, vector track, embed-vs-reference |
| `stores` / `warehouses` (lat/lon) | Bridge to the spatial track                        |
| `carts` / `sessions`              | Redis's natural workload                           |
| `categories` (parent/child)       | Recursive queries                                  |
| `price_history`                   | Time-based queries                                 |

_Status: stub — content to be added._
