# Graduate extension  (optional)

Only if you did the optional graduate-level extension.

## Multi-worker comparison

How you ran several workers (e.g. `uvicorn main:app --workers 4`), and how
the dictionary cache's hit rate compared with Redis's. Link the CSV and graph.

## Cache stampede

How you reproduced the stampede, the mechanism you added to reduce
duplicate database queries, and the database query count before and after.
