<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#emr-gotchas-and-limitations -->
# AWS Guide: EMR Gotchas and Limitations

-	💸❗**EMR costs** can pile up quickly since it involves lots of instances, efficiency can be poor depending on cluster configuration and choice of workload, and accidents like hung jobs are costly. See the section on EC2 cost management, especially the tips there about Spot instances. This blog post has additional tips, but was written prior to the shift to per-second billing.
-	💸 Beware of “double-dipping”. With EMR, you pay for the EC2 capacity and the service fees. In addition, EMR syncs task logs to S3, which means you pay for the storage and **PUT requests** at S3 standard rates. While the log files tend to be relatively small, every Hadoop job, depending on the size, generates thousands of log files that can quickly add up to thousands of dollars on the AWS bill. YARN’s log aggregation is not available on EMR.

Kinesis Streams
---
