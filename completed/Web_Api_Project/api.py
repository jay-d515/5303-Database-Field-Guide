# api.py  (required)
#
# The FastAPI server: it serves the page AND every route in section 3.2 of the
# assignment README. You may start from lessons/14-redis-cache/api.py, but
# your version must differ from it. At minimum it adds:
#
#   A4  GET /api/products?whole=true   whole-word search with a \b pattern
#   A6  sort=name_desc                 accepted by the Literal and the SORTS map
#   A8  an X-Cache-Key response header next to X-Cache
#
# And it keeps the section 3.3 rules: Decimal money, server-side pricing,
# Pydantic validation, atomic ids from `counters`, BSON converted before
# returning, re.escape on search text, and a cache that fails soft.
