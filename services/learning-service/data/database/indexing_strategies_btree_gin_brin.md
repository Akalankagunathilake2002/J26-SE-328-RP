# Relational Indexing Strategies: Deep Dive into B-Tree, GIN, and BRIN

## Comparing Specialized Index Structures
A database index is not one-size-fits-all. Selecting the wrong index type can degrade performance and inflate storage.

### 1. B-Tree (Balanced Tree)
- **Mechanics**: Self-balancing tree of 8KB disk pages. Internal pages store search keys and child page pointers; leaf pages store values and tuple identifiers (TIDs).
- **Time Complexity**: $O(\log N)$ traversal.
- **Ideal Queries**: Exact match (`=`), inequality range (`<`, `<=`, `>`, `>=`), prefix text search (`LIKE 'smith%'`), and sorting (`ORDER BY`).
- **Limitation**: Large memory footprint; poor fit for unstructured text, JSON documents, or multi-valued arrays.

### 2. GIN (Generalized Inverted Index)
- **Mechanics**: An inverted index mapping individual sub-elements (words, keys, array elements) to the set of rows containing them.
- **Ideal Queries**:
  - Full-Text Search: Tokenized English text matching (`to_tsvector @@ to_tsquery`).
  - JSONB Containment: Filtering nested JSON fields (`WHERE data @> '{"status": "active"}'`).
  - Array Operations: Array overlap and subset filters (`WHERE tags && ARRAY['java', 'backend']`).
- **Trade-off**: High write overhead and larger index size on disk. PostgreSQL mitigates this with a fast-update pending list that is periodically vacuumed.

### 3. BRIN (Block Range Index)
- **Mechanics**: Designed for massive append-only tables where data is physically ordered on disk (e.g., auto-incrementing IDs, timestamps).
- Instead of indexing every individual row TID, a BRIN index stores only the minimum and maximum values for physical blocks of pages (e.g. 128 disk pages per range).
- **Storage Comparison on 500 Million Rows**:
  - B-Tree index: ~12 GB in RAM.
  - BRIN index: ~64 KB (fits entirely in CPU L2 cache!).
- **Query Execution**: Traverses page ranges, skipping blocks whose min/max boundaries cannot satisfy the query filter.

### 4. Expression and Partial Indexes
- **Partial Index**: Indexes only a subset of rows satisfying a constant condition:
  ```sql
  CREATE INDEX idx_unprocessed_orders ON orders (created_at) WHERE status = 'PENDING';
  ```
  Reduces index size by 99% if only 1% of orders are pending.
- **Expression Index**: Indexes the result of a deterministic function:
  ```sql
  CREATE INDEX idx_users_lower_email ON users (LOWER(email));
  ```
  Allows case-insensitive queries without forcing sequential scans.
