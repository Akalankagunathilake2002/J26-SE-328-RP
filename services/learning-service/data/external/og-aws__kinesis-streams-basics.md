<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#kinesis-streams-basics -->
# AWS Guide: Kinesis Streams Basics

-	📒 Homepage ∙ Developer guide ∙ FAQ ∙ Pricing
-	**Kinesis Streams** (which used to be only called Kinesis, before Kinesis Firehose and Kinesis Analytics were launched) is a service that allows you to ingest high-throughput data streams for immediate or delayed processing by other AWS services.
- Kinesis Streams’ subcomponents are called **shards**. Each shard provides 1MB/s of write capacity and 2MB/s of read capacity at a maximum of 5 reads per second. A stream can have its shards programmatically increased or decreased based on a variety of metrics.
- All records entered into a Kinesis Stream are assigned a unique sequence number as they are captured. The records in a Stream are ordered by this number, so any time-ordering is preserved.
- This page summarizes key terms and concepts for Kinesis Streams.

Back to top :arrow_up:
