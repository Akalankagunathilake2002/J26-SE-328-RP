# Data Modeling Trade-offs: Relational PostgreSQL vs Document NoSQL

## The Relational vs NoSQL Paradigm Shift
- **Relational Databases (PostgreSQL, MySQL)**:
  - Enforce structured schemas, strict normalization (1NF, 2NF, 3NF), declarative foreign key constraints, and ACID transactions.
  - Optimized for data integrity, complex relational joins, and multi-entity transactional workflows (e.g. accounting, banking, inventory).
- **Document NoSQL (MongoDB, DynamoDB, Couchbase)**:
  - Store unstructured or semi-structured BSON/JSON documents.
  - Optimize for horizontal scalability across clusters, schema flexibility (rapid schema evolution without `ALTER TABLE` locks), and high write availability (BASE: Basically Available, Soft state, Eventual consistency).

## The CAP Theorem Reality
Under network partitioning ($P$), distributed databases must choose between:
- **Consistency ($C$)**: Every read receives the most recent write or an error (CP systems like HBase, CockroachDB).
- **Availability ($A$)**: Every non-failing node returns a response, though it may be stale (AP systems like Cassandra, DynamoDB).

Relational databases traditionally prioritize immediate consistency ($C$) and ACID durability over linear distributed horizontal scaling.

## Modern Convergence: PostgreSQL JSONB
Modern PostgreSQL bridges the gap between relational integrity and document flexibility via native `JSONB` support:
- Stores parsed, binary decomposed JSON with duplicate key removal and indexable fields.
- Accelerates complex queries over nested document attributes via **GIN Indexes**:
  ```sql
  CREATE INDEX idx_user_prefs ON users USING gin (preferences);
  SELECT * FROM users WHERE preferences @> '{"notifications": {"email": true}}';
  ```
- Permits joining structured relational tables (`orders`, `payments`) directly with unstructured JSON payloads within a single ACID transaction.
