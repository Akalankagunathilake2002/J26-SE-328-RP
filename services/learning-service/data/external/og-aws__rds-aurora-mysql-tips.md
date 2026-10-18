<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#rds-aurora-mysql-tips -->
# AWS Guide: RDS Aurora MySQL Tips

-	In order to take advantage of Aurora’s higher concurrency, applications should be configured with large database connection pools and should execute as many queries concurrently as possible. For example, Aurora servers have been tested to produce increasing performance on some OLTP workloads with up to 5,000 connections.
-	Aurora scales well with multiple CPUs and may require a large instance class for optimal performance.
-	The easiest migration path to Aurora is restoring a database snapshot from MySQL 5.6 or 5.7. The next easiest method is restoring a dump from a MySQL-compatible database such as MariaDB. For low-downtime migrations from other MySQL-compatible databases, you can set up an Aurora instance as a replica of your existing database. If none of those methods are options, Amazon offers a fee-based data migration service.
-	You can replicate from an Aurora cluster to MySQL or to another Aurora cluster. This requires binary logging to be enabled and is not as performant as native Aurora replication.
-	Because Aurora read replicas are the equivalent of a multi-AZ backup and they can be configured as zero-data-loss failover targets, there are fewer scenarios in which the creation of a multi-AZ Aurora instance is required.

Back to top :arrow_up:
