<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#dynamodb-tips -->
# AWS Guide: DynamoDB Tips

-	There is a **local version of DynamoDB** provided for developer use.
-	DynamoDB Streams provides an ordered stream of changes to a table. Use it to replicate, back up, or drive events off of data
-	DynamoDB can be used as a simple locking service.
-	DynamoDB indexing can include **primary keys**, which can either be a single-attribute hash key or a composite hash-key range. You can also query non-primary key attributes using **secondary indexes**.
-	**Data Types:** DynamoDB supports three data types – **number**, **string**, and **binary** – in both scalar and multi-valued sets. DynamoDB can also support **JSON**.
-	As of late 2017, DynamoDB supports both global tables and backup / restore functionality.

Back to top :arrow_up:
