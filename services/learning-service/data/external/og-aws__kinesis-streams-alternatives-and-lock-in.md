<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#in -->
# AWS Guide: Kinesis Streams Alternatives and Lock-in

-	🚪 Kinesis is most closely compared to Apache Kafka, an open-source data ingestion solution. It is possible to set up a Kafka cluster hosted on EC2 instances (or any other VPS), however you are responsible for managing and maintaining both Zookeeper and the Kafka brokers in a highly available configuration. Confluent has a good blog post with their recommendations on how to do this here, which has links on the bottom to several other blogs they have written on the subject.
-	⛓ Kinesis uses very AWS-specific APIs, so you should be aware of the potential future costs of migrating away from it, should you choose to use it.
-	An application that efficiently uses Kinesis Streams will scale the number of shards up and down based on the required streaming capacity. (Note there is no direct equivalent to this with Apache Kafka.)

Back to top :arrow_up:
