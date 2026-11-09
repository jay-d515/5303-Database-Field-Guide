---
title: "Redis Caching: When Does a Cache Actually Help?"
course: Advanced Database Systems
topic: Redis, Caching, Performance, and Scalability
level: Undergraduate / Graduate
prerequisites: Python, SQL, Basic Client-Server Architecture
---

# Redis Caching: When Does a Cache Actually Help?

## Overview

Modern applications frequently use caching to reduce database workloads, improve response times, and increase the number of requests a system can handle.

**Redis** is an in-memory data store commonly used as a cache, although it also supports other use cases, including messaging, counters, and data structures.

An important question is:

> How busy must a server become before adding Redis provides a measurable performance improvement?

The answer is that **there is no minimum number of users or requests**. The effectiveness of caching depends primarily on the cost of retrieving or computing data, the frequency with which results can be reused, and the overhead introduced by the caching system.

This handout explores these relationships through a small Python application, a relational database, and Redis.

## Learning Objectives

Upon completing this exercise, students should be able to:

1. Explain the purpose of caching in database-backed applications.
2. Describe the cache-aside design pattern.
3. Implement a Redis cache using Python.
4. Explain cache hits, cache misses, and time-to-live (TTL).
5. Compare database queries, application-level caching, and Redis caching.
6. Measure latency, throughput, and cache hit rates.
7. Identify situations where caching improves performance and where it may introduce unnecessary complexity.

---

# 1. Understanding the Problem

Consider an online store with a database containing 500,000 purchase records.

An application provides a leaderboard showing the ten customers who have spent the most money.

The SQL query might resemble:

```sql
SELECT
    customer_id,
    SUM(amount) AS total_spent
FROM purchases
GROUP BY customer_id
ORDER BY total_spent DESC
LIMIT 10;
```

Depending on database size, indexing, and available resources, this query may require significant processing.

Suppose the query takes 120 milliseconds to execute.

If 1,000 users request the leaderboard, the application may execute the same query 1,000 times.

However, imagine the leaderboard only needs to reflect purchases made within the last 30 seconds.

Is it necessary to execute the query for every request?

**No.** The application can store the query result temporarily and reuse it for subsequent requests.

This is the fundamental idea behind caching.

## 1.1 Without Caching

The application sends every request to the database.

```text
Client 1 ──┐
Client 2 ──┤
Client 3 ──┼──> Application ──> Database
Client 4 ──┤                     (SQL query)
Client 5 ──┘
```

Potential problems include increased database CPU usage, repeated query execution, increased response latency, and reduced capacity for other database operations.

## 1.2 With Redis Caching

The application checks Redis before querying the database.

```text
Clients
   |
   v
Application
   |
   v
Redis Cache
   |
   +── Cache HIT ──> Return cached result
   |
   +── Cache MISS
           |
           v
        Database
           |
           v
       Execute SQL
           |
           v
       Store in Redis
           |
           v
       Return result
```

This approach is called **cache-aside**, also known as lazy loading.

The application controls when information is retrieved from the database and stored in Redis.

---

# 2. Cache Hits, Misses, and Expiration

Three concepts are fundamental to caching.

### Cache Hit

A requested value already exists in Redis.

The application retrieves it without executing the original database query.

### Cache Miss

The requested value is not available in Redis.

The application retrieves it from the database and may store the result for future requests.

### Time-to-Live (TTL)

A TTL determines how long a cached value remains valid before Redis automatically expires it.

For example:

```python
cache.setex("leaderboard:top10", 30, result)
```

This stores a value with a 30-second TTL.

After expiration, a subsequent request will experience a cache miss.

A TTL does not guarantee that data remains current during those 30 seconds. Applications requiring immediate consistency may need explicit cache invalidation.

---

# 3. When Does Redis Improve Performance?

Caching introduces overhead. Accessing Redis requires communication, serialization, and data retrieval.

Consequently, Redis is not automatically faster than every database query.

Consider the following hypothetical response times:

| Operation                      | Execution Time |
| ------------------------------ | -------------: |
| Indexed PostgreSQL lookup      |         0.5 ms |
| Complex PostgreSQL aggregation |         120 ms |
| Redis cache lookup             |           1 ms |
| Python dictionary lookup       |       0.001 ms |

These values are illustrative rather than guaranteed benchmarks.

Notice that the indexed PostgreSQL lookup is faster than the Redis lookup in this example.

Adding Redis to such a query may actually reduce performance.

However, caching the expensive aggregation could reduce the response time from approximately 120 milliseconds to 1 millisecond on a cache hit.

That represents a 120-fold reduction in latency for that request.

## 3.1 A Mathematical Model

Let:

- \(D\) = Database query execution time
- \(C\) = Cache lookup time
- \(H\) = Cache hit rate, expressed as a fraction

Without caching:

$$
T_{\text{database}} = D
$$

With caching:

$$
T_{\text{cache}} = C + (1-H)D
$$

This model assumes that cache misses require the original database query and ignores cache population overhead, concurrency, and other operational costs.

Caching improves average response time when:

$$
C+(1-H)D < D
$$

Rearranging:

$$
\boxed{H > \frac{C}{D}}
$$

### Example

Suppose:

- Database query: 100 ms
- Redis lookup: 1 ms
- Cache hit rate: 90%

Then:

$$
T_{\text{cache}} = 1 + (1-0.90)(100)
$$

$$
T_{\text{cache}} = 11 \text{ ms}
$$

The average response time decreases from 100 milliseconds to approximately 11 milliseconds.

This is roughly a ninefold improvement.

The theoretical break-even hit rate is:

$$
H > \frac{1}{100} = 0.01
$$

Therefore, a hit rate above 1% would improve average latency under these assumptions.

**Important:** A mathematical latency improvement does not automatically justify the complexity of maintaining an additional service.

---

# 4. Building a Redis Caching Experiment

The following experiment uses:

- Python 3
- FastAPI
- SQLite
- Redis
- Docker

PostgreSQL may be substituted for SQLite in a more advanced version.

## 4.1 Install Dependencies

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the Python packages:

```bash
pip install fastapi uvicorn redis
```

Start Redis using Docker:

```bash
docker run -d \
  --name redis-lab \
  -p 127.0.0.1:6379:6379 \
  redis:7
```

Verify that Redis is running:

```bash
docker exec redis-lab redis-cli ping
```

Expected output:

```text
PONG
```

## 4.2 Create a Sample Database

Create a file named `setup_db.py`:

```python
import random
import sqlite3

random.seed(42)

with sqlite3.connect("shop.db") as db:
    db.execute("DROP TABLE IF EXISTS purchases")

    db.execute("""
        CREATE TABLE purchases (
            purchase_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            amount REAL
        )
    """)

    rows = [
        (
            random.randint(1, 10000),
            round(random.uniform(5, 500), 2)
        )
        for _ in range(500000)
    ]

    db.executemany("""
        INSERT INTO purchases (customer_id, amount)
        VALUES (?, ?)
    """, rows)

print("Created 500,000 purchase records.")
```

Execute:

```bash
python setup_db.py
```

The database now contains 500,000 purchases distributed among 10,000 customers.

## 4.3 Implement the Application

Create `main.py`:

```python
import json
import sqlite3
import time

import redis
from fastapi import FastAPI

app = FastAPI()

cache = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)


def expensive_query():
    # Artificial latency for the initial experiment.
    time.sleep(0.100)

    with sqlite3.connect("shop.db") as db:
        return db.execute("""
            SELECT customer_id, SUM(amount)
            FROM purchases
            GROUP BY customer_id
            ORDER BY SUM(amount) DESC
            LIMIT 10
        """).fetchall()


@app.get("/leaderboard/no-cache")
def no_cache():
    return {
        "source": "database",
        "data": expensive_query()
    }


@app.get("/leaderboard/cached")
def cached():
    key = "leaderboard:top10"

    result = cache.get(key)

    if result is not None:
        return {
            "source": "redis",
            "data": json.loads(result)
        }

    result = expensive_query()

    cache.setex(
        key,
        30,
        json.dumps(result)
    )

    return {
        "source": "database",
        "data": result
    }
```

The artificial delay makes cache behavior easier to observe.

It does not simulate actual database CPU consumption and should be removed for later performance testing.

## 4.4 Run the Application

Start FastAPI:

```bash
uvicorn main:app --port 8000
```

Test the uncached endpoint:

```bash
curl localhost:8000/leaderboard/no-cache
```

Test the cached endpoint:

```bash
curl localhost:8000/leaderboard/cached
```

Repeat the cached request within 30 seconds.

The response should indicate whether the result came from Redis or the database.

## 4.5 Inspect Redis Directly

Open the Redis command-line interface:

```bash
docker exec -it redis-lab redis-cli
```

Inspect the cached key:

```redis
GET leaderboard:top10
```

Check its remaining lifetime:

```redis
TTL leaderboard:top10
```

Delete the cached entry:

```redis
DEL leaderboard:top10
```

The next API request should cause a cache miss.

---

# 5. Measuring Performance

A cache is only useful if its benefits can be measured.

Useful performance metrics include:

| Metric             | Description                                              |
| ------------------ | -------------------------------------------------------- |
| Latency            | Time required to complete one request                    |
| Throughput         | Number of requests completed per second                  |
| Cache hit rate     | Percentage of requests served from cache                 |
| Cache miss rate    | Percentage requiring the original data retrieval         |
| Database CPU usage | Processing resources consumed by the database            |
| p95 latency        | Response time at or below which 95% of requests complete |

Students should distinguish between average latency and percentile latency. A system can have an acceptable average response time while still producing extremely slow requests.

## 5.1 Initial Timing Experiment

Use `curl` to measure request duration:

```bash
curl -s -o /dev/null \
  -w "Time: %{time_total}s\n" \
  localhost:8000/leaderboard/no-cache
```

Repeat with:

```bash
curl -s -o /dev/null \
  -w "Time: %{time_total}s\n" \
  localhost:8000/leaderboard/cached
```

Record several measurements for each endpoint.

## 5.2 Suggested Test Cases

| Test | Query Type                   |  Cache TTL | Requests |
| ---- | ---------------------------- | ---------: | -------: |
| A    | No cache                     |          — |      100 |
| B    | Redis cache                  | 30 seconds |      100 |
| C    | Redis cache                  |  5 seconds |      100 |
| D    | Redis cache                  | 60 seconds |      100 |
| E    | Redis cache, frequent misses | 30 seconds |      100 |

For meaningful comparisons, control the request rate and duration. A TTL of 30 seconds does not guarantee a particular hit rate.

For more advanced testing, use a load generator such as Locust or k6 to simulate concurrent clients.

---

# 6. Redis vs. Python Dictionary Caching

Redis is not the only way to cache information.

A Python application can cache results directly in memory.

For example:

```python
local_cache = {}

def get_leaderboard():
    if "leaderboard" in local_cache:
        return local_cache["leaderboard"]

    result = expensive_query()

    local_cache["leaderboard"] = result

    return result
```

This is a simplified example without expiration or invalidation.

For a single-process application, a dictionary lookup may be faster than a Redis lookup because it avoids network communication and serialization.

So why use Redis?

## 6.1 Multiple Application Processes

Consider an application running four worker processes.

Each process maintains its own memory.

```text
Worker 1 ──> Dictionary Cache 1
Worker 2 ──> Dictionary Cache 2
Worker 3 ──> Dictionary Cache 3
Worker 4 ──> Dictionary Cache 4
```

A value cached by Worker 1 is not automatically available to Worker 2.

Redis provides a shared caching service:

```text
Worker 1 ──┐
Worker 2 ──┤
Worker 3 ──┼──> Redis
Worker 4 ──┘
```

All four workers can access the same cached values.

This makes Redis particularly useful in distributed and multi-process applications.

However, it also introduces network dependencies, memory requirements, and additional operational complexity.

---

# 7. Cache Invalidation and Consistency

Caching creates an important problem:

**What happens when the underlying database changes?**

Suppose Redis contains the top ten customers from 20 seconds ago.

A customer makes a large purchase that changes the leaderboard.

Until the cached result expires or is invalidated, the application may continue returning the old leaderboard.

Three common strategies are:

### Time-Based Expiration

Allow cached data to expire after a fixed TTL.

Simple to implement, but data may temporarily become stale.

### Explicit Invalidation

Delete or update a cached entry when relevant database records change.

This can improve freshness but requires careful coordination.

### Versioned Cache Keys

Use a version identifier in cache keys, such as:

```text
leaderboard:v1:top10
leaderboard:v2:top10
```

Changing versions can make older entries obsolete without immediately deleting them.

Each strategy has different tradeoffs involving consistency, complexity, and performance.

---

# 8. The Cache Stampede Problem

A cache stampede occurs when many requests simultaneously discover that a popular cached value is missing or expired.

Imagine 100 clients requesting the leaderboard at nearly the same moment.

```text
100 Requests
     |
     v
 Redis Cache
     |
     v
 Cache Miss
     |
     v
100 Database Queries
```

Instead of reducing database traffic, the application may suddenly generate a large burst of expensive queries.

Potential solutions include distributed locking, request coalescing, proactive cache refresh, and serving temporarily stale data while refreshing.

A cache stampede demonstrates why caching is more than simply adding `GET` and `SET` commands.

---

# 9. Laboratory Assignment

## Objective

Determine when Redis caching provides measurable benefits compared with querying a relational database directly.

### Part A: Baseline Performance

Run the application without caching.

Measure average response time, minimum and maximum response times, and throughput.

Repeat with different numbers of requests.

### Part B: Redis Caching

Enable Redis caching.

Measure the same metrics and record cache hits and misses.

Compare cold-cache and warm-cache performance.

### Part C: TTL Experiment

Test TTL values of 5, 30, and 60 seconds.

Determine how TTL affects cache hit rate, database query count, and data freshness.

### Part D: Application-Level Caching

Implement a Python dictionary cache with expiration behavior comparable to Redis.

Compare its performance against Redis for a single application process.

### Part E: Query Complexity

Remove the artificial `time.sleep()` delay.

Compare caching for a simple indexed lookup and a more expensive aggregation.

Use actual measurements to determine which query benefits most.

### Part F: Analysis

Prepare a table containing measured results.

| Strategy          | Avg. Latency | p95 Latency | Requests/sec | Hit Rate |
| ----------------- | -----------: | ----------: | -----------: | -------: |
| No cache          |              |             |              |      N/A |
| Python dictionary |              |             |              |          |
| Redis, 5s TTL     |              |             |              |          |
| Redis, 30s TTL    |              |             |              |          |
| Redis, 60s TTL    |              |             |              |          |

Discuss whether the results support the mathematical model introduced earlier.

---

# 10. Discussion Questions

1. Why might Redis improve the performance of an expensive aggregation but not an indexed database lookup?
2. Does caching become beneficial only after a system reaches a certain number of users? Explain.
3. Why might a Python dictionary outperform Redis in a single-process application?
4. What advantages does Redis offer when an application uses multiple workers or servers?
5. What happens when the database changes but the cached result has not expired?
6. How does TTL influence the tradeoff between performance and data freshness?
7. What is a cache stampede, and how might it be prevented?
8. Can caching reduce database load without significantly improving user-visible latency?
9. Why should benchmarks include p95 latency rather than only average latency?
10. Under what circumstances would adding Redis be an unnecessary complication?

---

# 11. Deliverables

Submit a GitHub repository containing the application source code, database setup script, dependency list, and instructions for running the experiment.

Include a `README.md` with:

- A description of the caching strategies implemented.
- A table of benchmark results.
- At least one graph comparing performance.
- An explanation of observed cache hits and misses.
- A discussion of the conditions under which Redis was beneficial.
- A conclusion supported by measurements rather than assumptions.

## Optional Graduate-Level Extension

Implement a multi-worker FastAPI deployment and compare local dictionary caching against shared Redis caching.

Investigate whether increasing the number of application workers changes the cache hit rate or performance characteristics.

For additional credit, reproduce a cache stampede and implement a mechanism to reduce duplicate database queries.

---

# 12. Key Takeaways

Caching is a technique for avoiding repeated work.

Redis can provide significant performance improvements when expensive operations produce results that can be reused across multiple requests.

However, Redis is not universally faster than a relational database, and it is not always preferable to application-level caching.

The value of a cache depends on query cost, cache hit rate, data freshness requirements, concurrency, and system architecture.

**The central engineering principle is simple:**

> Cache results when the cost of retrieving and maintaining cached data is lower than the cost of repeatedly performing the original operation.

A system with ten users may benefit from caching an expensive computation, while a system serving thousands of unique, inexpensive queries may gain very little.

Performance optimization should begin with measurement, not assumptions.

**Remember: adding another server is not automatically an optimization. Sometimes it is simply another server to maintain.**