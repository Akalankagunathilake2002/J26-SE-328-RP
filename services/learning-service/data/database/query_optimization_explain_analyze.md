# SQL Query Performance Tuning with EXPLAIN ANALYZE

## Inside the Cost-Based Query Optimizer
When a SQL query is submitted, the PostgreSQL Query Planner evaluates dozens of candidate execution trees, assigning estimated arbitrary cost units based on table statistics collected by `ANALYZE` (stored in `pg_statistic` and `pg_stats`).
- `EXPLAIN`: Shows the optimizer's estimated execution plan and cost without running the query.
- `EXPLAIN (ANALYZE, BUFFERS, VERBOSE)`: Actually executes the query, recording real-world elapsed time (ms), rows returned, loops executed, and shared memory buffer page hits/reads.

## Reading Plan Nodes and Cost Metrics
A sample plan node output:
```text
Index Scan using idx_users_email on users  (cost=0.42..8.44 rows=1 width=72) (actual time=0.034..0.035 rows=1 loops=1)
  Index Cond: (email = 'student@skillbridge.edu'::text)
  Buffers: shared hit=4
```
- `cost=0.42..8.44`: `0.42` is the startup cost before the node can return its first row; `8.44` is the total cost to return all estimated rows (`rows=1`).
- `actual time=0.034..0.035`: The actual physical execution time in milliseconds.
- `Buffers: shared hit=4`: All 4 required 8KB pages were already present in `shared_buffers` RAM cache (zero physical disk reads).

## Common Scan Types
1. **Seq Scan (Sequential Scan)**: Reads every page of the table from start to finish. Efficient for retrieving > 20% of the table; disastrous for large tables filtering for a specific entity ID.
2. **Index Scan**: Traverses the B-Tree index to locate matching TIDs, then fetches the actual table tuple pages from heap storage to retrieve unindexed columns.
3. **Index Only Scan**: All requested columns in the `SELECT` list are present within the index itself, avoiding table heap page lookups (assuming visibility map confirms rows are all-visible).
4. **Bitmap Index Scan / Bitmap Heap Scan**: Gathers all matching TIDs from one or more indexes into an in-memory bitmap, sorts them by physical disk location, and reads heap pages sequentially, minimizing random disk head movement.

## Join Strategies in Execution Plans
- **Nested Loop**: Iterates through outer table rows, searching the inner table index for each row. Optimal when the outer set is small (< 100 rows).
- **Hash Join**: Builds an in-memory hash table of the smaller relation, then streams the larger relation to find matches. Fast for medium-to-large unindexed sets.
- **Merge Join**: Both relations are pre-sorted on the join key (or scanned via an index), then merged in a single linear pass. Ideal for large sorted datasets.
