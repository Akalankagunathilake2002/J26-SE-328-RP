<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#kinesis-streams-tips -->
# AWS Guide: Kinesis Streams Tips

-	The KCL (Kinesis Client Library) provides a skeleton interface for Java, Node, Python, Ruby and .NET programs to easily consume data from a Kinesis Stream. In order to start consuming data from a Stream, you only need to provide a config file to point at the correct Kinesis Stream, and functions for initialising the consumer, processing the records, and shutting down the consumer within the skeletons provided.
	- The KCL uses a DynamoDB table to keep track of which records have been processed by the KCL. This ensures that all records are processed “at least once”. It is up to the developer to ensure that the program can handle doubly-processed records.
	- The KCL also uses DynamoDB to keep track of other KCL “workers”. It automatically shares the available Kinesis Shards across all the workers as equally as possible.

Back to top :arrow_up:
