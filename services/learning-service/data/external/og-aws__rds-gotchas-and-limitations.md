<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#rds-gotchas-and-limitations -->
# AWS Guide: RDS Gotchas and Limitations

-	⏱RDS instances run on EBS volumes (either general-purpose or provisioned IOPS), and hence are constrained by EBS performance.
-	🔸Verify what database features you need, as not everything you might want is available on RDS. For example, if you are using Postgres, check the list of supported features and extensions. If the features you need aren't supported by RDS, you'll have to deploy your database yourself.
-	🔸If you use the failover support offered by RDS, keep in mind that it is based on DNS changes, and make sure that your client reacts to these changes appropriately. This is particularly important for Java, given how its DNS resolver’s TTL is configured by default.
-	🔸**DB migration to RDS:** While importing your database into RDS ensure you take into consideration the maintenance window settings. If a backup is running at the same time, your import can take a considerably longer time than you would have expected.
-	Database sizes are limited to **6TB** for all database engines except for SQL Server which has a **4TB** limit and Aurora which supports up to **64TB** databases.

RDS MySQL and MariaDB
---------------------
