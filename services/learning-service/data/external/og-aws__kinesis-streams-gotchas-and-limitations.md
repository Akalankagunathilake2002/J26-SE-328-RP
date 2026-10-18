<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#kinesis-streams-gotchas-and-limitations -->
# AWS Guide: Kinesis Streams Gotchas and Limitations

- 🔸⏱  Kinesis Streams’ shards each only permit 5 reads per second. If you are evenly distributing data across many shards, your read limit for the Stream will remain at 5 reads per second on aggregate, as each consuming application will need to check every single shard for new records. This puts a hard limit on the number of different consuming applications possible per Stream for a given maximum read latency.
   - For example, if you have 5 consuming applications reading data from one Stream with any number of shards, they cannot read with a latency of less than one second, as each of the 5 consumers will need to poll *each shard* every second, reaching the cap of 5 reads per second per shard.
	- This blog post further discusses the performance and limitations of Kinesis in production.
-	💸 **Kinesis Streams are not included in the free tier.** Make sure if you do any experimentation with it on a personal account, you shut down the stream or it may run up unexpected costs (~$11 per shard-month.)

Kinesis Firehose
---

Back to top :arrow_up:
