# Relational Database Indexing and Performance Optimization

## Why Indexing Matters
Without an index, a database management system (such as PostgreSQL or MySQL) must perform a Full Table Scan (sequential scan), inspecting every row in the storage pages to satisfy a query filter. As tables grow to millions of rows, sequential scans cause catastrophic $O(N)$ disk I/O bottlenecks.

An index creates an auxiliary data structure that maps column values to row pointers (TIDs/CTIDs in PostgreSQL), reducing search complexity to $O(\log N)$.

## Index Data Structures
1. **B-Tree (Balanced Tree)**: The default and most versatile index type in relational databases. Ideal for equality (`=`) and range queries (`<`, `<=`, `>`, `>=`, `BETWEEN`). B-Trees remain balanced as data is inserted, deleted, and updated.
2. **Hash Index**: Optimized exclusively for exact equality lookups (`=`). Does not support range scanning.
3. **GIN (Generalized Inverted Index)**: Designed for composite items like JSONB documents, arrays, and full-text search.
4. **HNSW (Hierarchical Navigable Small World)**: A specialized vector index in pgvector enabling ultra-fast approximate nearest neighbor (ANN) search over high-dimensional vector embeddings with logarithmic scaling.

## Indexing Trade-offs & Best Practices
- **Write Overhead**: Every `INSERT`, `UPDATE`, and `DELETE` on a table requires the database to update the corresponding indexes, incurring disk write amplification.
- **Index Selectivity**: Index columns with high selectivity (columns where values are unique or have a high number of distinct values).
- **Composite Index Column Order**: Put columns used in equality filters first, followed by range scan filters (the "Equality then Range" rule).
- **Query Analysis**: Use `EXPLAIN ANALYZE` in PostgreSQL to inspect the query planner's execution plan and verify index usage.
