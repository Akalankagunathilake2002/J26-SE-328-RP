# Distributed Message Queues: Apache Kafka vs RabbitMQ

## Architectural Paradigms: Log-Centric vs Broker-Centric
1. **Apache Kafka (Distributed Append-Only Commit Log)**:
   - Kafka stores messages in durable, partitioned disk logs retained for a configurable time window (e.g., 7 days), regardless of consumer read status.
   - Consumers maintain their own read offsets (`__consumer_offsets`), allowing independent replaying, batch reading, and event sourcing.
   - Unmatched horizontal throughput: Millions of events/second via sequential disk I/O and zero-copy OS paging (`sendfile`).

2. **RabbitMQ (AMQP Smart-Broker / Message Queue)**:
   - RabbitMQ utilizes exchange routing rules (Direct, Topic, Fanout, Headers) to route messages into queues.
   - Messages are tracked on the broker and deleted once acknowledged (`ACK`) by a consumer worker.
   - Excels at complex transactional routing, prioritization, and precise job queue orchestration.

## Kafka Partitioning and Consumer Scaling
- A Kafka topic is divided into $N$ partitions. Partitions represent the fundamental unit of parallelism.
- **Message Ordering**: Kafka guarantees strict chronological ordering *within a single partition*, keyed by `hash(message_key) % num_partitions`.
- **Consumer Groups**:
  - Each partition is assigned to exactly one consumer instance within a consumer group.
  - If a topic has 6 partitions and a consumer group has 3 instances, each instance processes 2 partitions.
  - Adding consumer instances beyond the partition count leaves excess consumers idle.

## Message Delivery Semantics
- **At-Most-Once**: The consumer commits its offset *before* processing the message. If the worker crashes mid-processing, the message is lost.
- **At-Least-Once**: The consumer commits its offset *after* successfully processing the message. If the worker crashes before the commit, the message is reprocessed upon restart. Requires **idempotent** consumers (e.g. database unique constraints or deduplication keys).
- **Exactly-Once Processing (EOS)**: Achieved via transactional producers and two-phase commit protocols across Kafka streams and state stores.
