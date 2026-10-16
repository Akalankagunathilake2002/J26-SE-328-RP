# Transaction Isolation Levels, Concurrency Anomalies, and ACID Mechanics

## ACID Guarantees in Relational Systems
Relational databases enforce four foundational transaction guarantees:
- **Atomicity**: An entire transaction completes successfully, or all changes are rolled back.
- **Consistency**: Transactions transition the database from one valid state to another, enforcing constraints, foreign keys, and triggers.
- **Isolation**: Concurrent transactions execute without interfering with one another.
- **Durability**: Once committed, transaction mutations persist even across immediate power loss or operating system crashes (via Write-Ahead Logging / WAL).

## Concurrency Anomalies (Phenomena)
1. **Dirty Read**: Transaction A modifies a row without committing. Transaction B reads the uncommitted value. Transaction A rolls back. Transaction B acted on non-existent data.
2. **Non-Repeatable Read (Fuzzy Read)**: Transaction A reads a row. Transaction B updates that same row and commits. Transaction A re-reads the row and observes a different value within the same transaction.
3. **Phantom Read**: Transaction A reads a range of rows matching a condition (`WHERE age > 30`). Transaction B inserts a new row matching the condition and commits. Transaction A re-executes the range query and sees an extra row ("phantom").
4. **Serialization Anomaly**: Concurrent transaction outcomes cannot be reproduced by any possible serial execution sequence (e.g. Write Skew in medical doctor on-call scheduling).

## ANSI SQL Isolation Levels vs PostgreSQL MVCC Implementation
| Isolation Level | Dirty Read | Non-Repeatable Read | Phantom Read | Serialization Anomaly |
|---|---|---|---|---|
| **Read Uncommitted** | Possible (prevented in PG) | Possible | Possible | Possible |
| **Read Committed** | Prevented | Possible | Possible | Possible |
| **Repeatable Read** | Prevented | Prevented | Prevented (in PG via MVCC) | Possible (Write Skew) |
| **Serializable** | Prevented | Prevented | Prevented | Prevented |

## How PostgreSQL Multi-Version Concurrency Control (MVCC) Works
PostgreSQL never locks rows for reading (`Readers never block Writers, and Writers never block Readers`).
- Every row contains hidden metadata columns: `xmin` (ID of creating transaction) and `xmax` (ID of deleting/updating transaction).
- When a transaction runs at `Repeatable Read`, it captures a consistent **Snapshot** of the database at the start of its first query. All reads see only rows whose `xmin` was committed before the snapshot began, completely eliminating Non-Repeatable and Phantom reads without read locks.
- **Serializable Snapshot Isolation (SSI)**: Tracks read-write dependency locks (SIREAD locks) in memory. If a dangerous cycle of dependencies is detected among concurrent transactions, PostgreSQL aborts one with `ERROR: could not serialize access due to read/write dependencies`.
