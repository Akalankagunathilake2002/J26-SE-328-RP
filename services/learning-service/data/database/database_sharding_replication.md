# Database High Availability: Primary-Replica Replication and Sharding

## Read Scaling via Replication Topologies
When read query volume outgrows a single database node's CPU capacity, systems separate write and read paths using Primary-Replica streaming replication.

### Asynchronous vs Synchronous Replication
1. **Asynchronous Streaming Replication**:
   - The Primary executes transactions, commits locally, writes to the Write-Ahead Log (WAL), and returns success to the client immediately. A background WAL sender streams log records to Replicas.
   - *Advantage*: High write throughput and low commit latency.
   - *Risk (Replication Lag)*: Reads hitting the Replica immediately after a write may read stale data (lack of Read-Your-Own-Writes consistency). If the Primary crashes before WAL sync, unstreamed transactions are lost (RPO > 0).

2. **Synchronous Replication**:
   - The Primary holds the commit response until at least one Replica acknowledges receiving and flushing the WAL to disk.
   - *Advantage*: Zero data loss (RPO = 0) upon primary failover.
   - *Drawback*: Write latency is bound to network round-trip time between Primary and Replica.

## Write Scaling via Horizontal Sharding
When write volume or data storage exceeds the capacity of the largest available vertical database instance (e.g. > 10 TB with 50,000 writes/sec), horizontal sharding partitions rows across multiple independent physical database instances (shards).

### Sharding Routing Strategies
1. **Range-Based Sharding**: Assigns ranges of keys to specific shards (e.g., Users A-M on Shard 1, N-Z on Shard 2). Vulnerable to severe write skew if new entries disproportionately hit one range.
2. **Hash-Based Sharding**: Applies a cryptographic hash to the shard key:
   $$\text{Shard ID} = \text{hash}(\text{entity\_id}) \pmod{\text{Total Shards}}$$
   Distributes writes uniformly across shards.
3. **Consistent Hashing**: Maps nodes and keys to a continuous $2^{32}$ circular ring. Adding or removing a shard node requires rebalancing only $K / N$ keys rather than reshuffling the entire database.

### Challenges of Sharded Architectures
- **Cross-Shard Joins**: Joining tables located on different physical shards requires distributed map-reduce queries or denormalization.
- **Distributed Two-Phase Commit (2PC)**: Transactions spanning multiple shards require coordinator locks, creating latency overhead and vulnerability to coordinator failure.
