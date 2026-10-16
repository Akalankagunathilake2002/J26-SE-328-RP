# PostgreSQL Table Partitioning and Large-Scale Data Management

## Why Partitioning is Essential
When relational tables grow beyond hundreds of gigabytes (tens of millions of rows), two critical bottlenecks emerge:
1. **Index Size Exceeds RAM**: Once B-Tree indexes exceed the PostgreSQL buffer cache (`shared_buffers`), index traversals require frequent disk page fetches, causing performance degradation.
2. **Vacuum and Maintenance Lock Contention**: Routine `VACUUM`, `ANALYZE`, and index rebuilding operations consume massive I/O bandwidth and can lock entire tables.

Partitioning decomposes a large logical table into smaller, physically independent child tables (partitions) while maintaining a single unified query interface.

## Partitioning Strategies in PostgreSQL
1. **Range Partitioning**:
   - Divides rows into distinct, non-overlapping ranges of a key column (commonly timestamp or integer ranges).
   - Ideal for timeseries logs, audit trails, and financial transactions partitioned by month (`orders_2026_01`, `orders_2026_02`).
2. **List Partitioning**:
   - Maps rows based on explicit lists of discrete key values (e.g., geographic country code `US`, `EU`, `APAC`).
3. **Hash Partitioning**:
   - Distributes rows evenly across a fixed number of partitions using a hash function on the partition key modulus (`hash(user_id) % 16`).
   - Ensures uniform data distribution without hotspots.

## Partition Pruning Optimization
The primary query optimization unlocked by partitioning is **Partition Pruning**.
When a SQL query contains a `WHERE` clause filtering on the partition key:
```sql
SELECT * FROM audit_logs WHERE created_at >= '2026-06-01' AND created_at < '2026-07-01';
```
The PostgreSQL query planner automatically identifies and scans *only* the matching child table (`audit_logs_2026_06`), skipping all other partition tables entirely. This reduces disk I/O from scanning hundreds of gigabytes down to a few hundred megabytes.

## Data Retention and Zero-Downtime Archival
Archiving or deleting old data in non-partitioned tables using `DELETE FROM audit_logs WHERE created_at < '2025-01-01'` causes massive WAL write spikes and table bloat.
With table partitioning, old data is purged instantly with zero I/O overhead:
```sql
ALTER TABLE audit_logs DETACH PARTITION audit_logs_2024_12;
DROP TABLE audit_logs_2024_12;
```
This drops the physical storage files in milliseconds without requiring row-by-row deletions or table vacuuming.
