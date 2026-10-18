<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#dynamodb-gotchas-and-limitations -->
# AWS Guide: DynamoDB Gotchas and Limitations

-	🔸 DynamoDB doesn’t provide an easy way to bulk-load data (it is possible through Data Pipeline) and this has some unfortunate consequences. Since you need to use the regular service APIs to update existing or create new rows, it is common to temporarily turn up a destination table’s write throughput to speed import. But when the table’s write capacity is increased, DynamoDB may do an irreversible split of the partitions underlying the table, spreading the total table capacity evenly across the new generation of tables. Later, if the capacity is reduced, the capacity for each partition is also reduced but the total number of partitions is not, leaving less capacity for each partition. This leaves the table in a state where it much easier for hotspots to overwhelm individual partitions.
-	🔸 It is important to make sure that DynamoDB resource limits are compatible with your dataset and workload. For example, the maximum size value that can be added to a DynamoDB table is 400 KB (larger items can be stored in S3 and a URL stored in DynamoDB).
-	🔸 Dealing with **time series data** in DynamoDB can be challenging. A global secondary index together with down sampling timestamps can be a possible solution as explained here.
-	🔸 When setting up fine grained policies for access to DynamoDB tables, be sure to include their secondary indices in the policy document as well.

ECS
---
