# Database Connection Pooling and Resource Optimization

## Overhead of Non-Pooled Database Connections
Establishing a raw database connection requires multiple network round-trips:
1. TCP 3-way handshake (`SYN`, `SYN-ACK`, `ACK`).
2. TLS cryptographic handshake (key exchange and certificate verification).
3. Database engine authentication and role verification.
4. Process or thread allocation on the database server.

Under high concurrency (e.g. 5,000 requests/sec), establishing and tearing down physical TCP connections per HTTP request causes severe latency spikes and quickly exhausts database file descriptors, resulting in `FATAL: remaining connection slots are reserved for non-privileged users`.

## Architecture of HikariCP and Connection Pools
A connection pool (such as HikariCP in Spring Boot or asyncpg pool in Python) initializes and maintains a fixed reservoir of active, authenticated TCP sockets:
- **Connection Borrowing**: When an application thread begins a transaction, it borrows an idle socket from the pool in microseconds ($O(1)$ lock-free handoff).
- **Transaction Execution**: The thread issues queries and transactions through the borrowed connection.
- **Connection Return**: Upon transaction commit or rollback, the thread returns the socket to the pool rather than closing it.

## Sizing Formula and Production Tuning
Contrary to naive assumptions, larger pool sizes degrade performance due to disk I/O thrashing and CPU context-switching on the database server.

The PostgreSQL recommended pool sizing formula:
$$\text{Pool Size} = (2 \times \text{CPU Cores}) + \text{Disk Spindles}$$

For modern NVMe storage, a 16-core database server frequently achieves maximum throughput with just 32 to 50 active connections.

### Key Operational Metrics
- **Connection Timeout (`connectionTimeout`)**: Max wait time (e.g., 2,000ms) for an application thread to obtain a connection before throwing a timeout exception.
- **Max Lifetime (`maxLifetime`)**: Periodically cycles out physical connections to prevent memory bloat and stale firewall NAT drops.
- **Leak Detection Threshold (`leakDetectionThreshold`)**: Logs stack traces if a borrowed connection is not returned within a threshold (e.g. 5,000ms), identifying unclosed transactions.
