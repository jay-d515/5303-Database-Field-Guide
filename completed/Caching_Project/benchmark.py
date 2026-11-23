# benchmark.py  (required in some form: see README variations)
#
# Sends a controlled number of requests to one endpoint and records, per run:
#   average, min, max, and p95 latency; requests per second; hits and misses.
#
# Writes one CSV per lab part into results/. Control the request rate and
# duration (handout 5.2): a TTL alone doesn't determine the hit rate.
