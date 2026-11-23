# main.py  (required: "application source code")
#
# The FastAPI app (handout section 4.3), grown to cover every lab part:
#
#   Part A  an endpoint with no cache
#   Part B  a Redis cache-aside endpoint that reports whether each response
#           came from redis or the database
#   Part C  a way to change the TTL (5, 30, 60 s) without editing code,
#           e.g. a query parameter or an environment variable
#   Part D  a Python dictionary cache WITH expiration comparable to Redis
#   Part E  a simple indexed lookup and the expensive aggregation, each with
#           and without caching, and the time.sleep() delay removed
#
# You also need some way to count hits and misses: counters in the app, an
# endpoint that reports them, or the "source" field tallied by benchmark.py.
