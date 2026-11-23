# api.py  (required)
#
# Your MODIFIED copy of the api.py you were given (from the latest lesson
# version you worked through, e.g. lessons/13-filter-and-sort/api.py).
#
# What should be different from the original:
#   - Every route returns the standardized envelope by calling your reusable
#     mechanism from responses.py. No route builds the envelope dict by hand.
#   - GET /api/products accepts q, limit (1-100, default 100), and offset
#     (>= 0, default 0). Pagination happens IN the MongoDB query, the count
#     uses the same filter, and the sort is deterministic (with a unique
#     tie-breaker).
#   - POST /api/customers and POST /api/purchases still return HTTP 201.
#   - Exception handlers are registered so HTTPException and
#     RequestValidationError both come back in the standard envelope
#     (unless you put them in errors.py; see the README variations).
#
# What should NOT change:
#   - The MongoDB document structure.
#   - The routes' paths, and the limits/behavior of every route other than
#     GET /api/products.
