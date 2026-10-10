# API Rate Limiting and Traffic Throttling Algorithms

## Purpose of Rate Limiting
Rate limiting protects backend microservices from Denial-of-Service (DoS) attacks, brute-force credential stuffing, abusive web scrapers, and accidental client loops. It enforces fairness across multi-tenant API tiers and prevents unexpected cloud infrastructure cost overruns.

## Core Rate Limiting Algorithms
1. **Fixed Window Counter**:
   - Divides time into fixed intervals (e.g. 1 minute). Counts requests per client IP or API key.
   - *Vulnerability (Boundary Burst)*: If a user sends 100 requests at 11:59:59 and another 100 requests at 12:00:01, they successfully deliver 200 requests within 2 seconds without triggering the 100 req/min limit.

2. **Sliding Window Log**:
   - Records every request timestamp in a Redis sorted set (`ZADD`).
   - Removes entries older than the current window (`ZREMRANGEBYSCORE`), then counts remaining elements (`ZCARD`).
   - *Advantage*: Absolute mathematical accuracy.
   - *Trade-off*: High memory footprint under heavy traffic volumes.

3. **Sliding Window Counter (Approximation)**:
   - Blends the request count of the previous window and the current window using an elapsed time weighting factor:
     $$\text{Estimated Count} = \text{Count}_{\text{current}} + \text{Count}_{\text{previous}} \times (1 - \text{fraction\_elapsed})$$
   - Memory-efficient and resilient to boundary spikes.

4. **Token Bucket**:
   - A bucket has a maximum capacity $C$ and refills at a steady rate of $R$ tokens per second.
   - Each request consumes 1 token. If the bucket is empty, requests are rejected with `HTTP 429 Too Many Requests`.
   - *Key Advantage*: Accommodates short legitimate bursts up to capacity $C$ while enforcing long-term average throughput $R$.

5. **Leaky Bucket**:
   - Requests enter a FIFO queue of capacity $C$ and leak out at a constant, fixed rate $R$.
   - *Key Advantage*: Completely smooths bursty traffic into a predictable, steady output flow to downstream databases.

## Distributed Rate Limiting with Redis & Lua
In clustered environments with multiple API Gateway nodes, local in-memory counters fail because requests from the same user hit different gateway pods.
Production systems use centralized Redis instances executing atomic Lua scripts:
```lua
local current = redis.call('INCR', KEYS[1])
if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
if current > tonumber(ARGV[2]) then
    return 0 -- Rejected
end
return 1 -- Allowed
```
The Lua script executes atomically within Redis's single-threaded event loop, preventing race conditions.
