# High-Performance Caching Patterns with Redis

## Caching Access Topologies
1. **Cache-Aside (Lazy Loading)**:
   - The application first queries the Redis cache.
   - If a **Cache Hit** occurs, data is returned in < 2ms.
   - If a **Cache Miss** occurs, the application queries the relational database, populates Redis with an expiration TTL, and returns the result to the caller.
   - *Advantage*: The cache contains only actively requested keys, minimizing RAM consumption.

2. **Write-Through**:
   - Every mutation updates Redis and the primary database synchronously before returning HTTP 200.
   - *Advantage*: Guarantees cache consistency and eliminates cold-start cache misses on newly written records.

3. **Write-Behind (Write-Back)**:
   - The application writes directly to Redis, and an asynchronous daemon batches updates to the SQL database.
   - *Advantage*: Unmatched write throughput, with the trade-off of possible data loss during sudden cache node failure.

## Mitigating Cache Failures at Scale
- **Cache Stampede (Thundering Herd)**: When a high-traffic key (e.g. homepage catalog) expires, thousands of concurrent threads experience simultaneous cache misses and overwhelm the relational database.
  - *Solution*: Probabilistic early expiration (XFetch algorithm) or distributed mutual exclusion locks (`SET key lock NX EX 5`) so only one thread recomputes the query while others wait.
- **Cache Penetration**: Malicious or invalid queries for non-existent IDs bypass the cache and hit the database repeatedly.
  - *Solution*: Store a sentinel null value with a short TTL (e.g., 60 seconds) or configure an upstream Bloom Filter to filter non-existent IDs.
- **Cache Avalanche**: Hundreds of keys initialized simultaneously expire at the exact same minute.
  - *Solution*: Add a randomized jitter offset (e.g. $\text{TTL} \pm 10\%$) to distribute expiration windows uniformly.

## Eviction Policies
When Redis memory reaches `maxmemory`, eviction policies govern key deletion:
- `allkeys-lru`: Evicts least-recently used keys across the entire keyspace.
- `volatile-ttl`: Evicts keys with an explicit TTL that are closest to expiration.
- `noeviction`: Returns out-of-memory errors on new write commands while preserving existing data.
