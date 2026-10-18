<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#rds-mysql-and-mariadb-gotchas-and-limitations -->
# AWS Guide: RDS MySQL and MariaDB Gotchas and Limitations

-	🔸**No SUPER privileges.** RDS provides some stored procedures to perform some tasks that require SUPER privileges such as starting or stopping replication.
-	🔸You can replicate to non-RDS instances of MySQL, but replication to these instances will break during AZ failovers.
-	🔸There is no ability to manually CHANGE MASTER on replicas, so they must all be rebuilt after a failover of the master.
-	🔸Most global options are exposed only via DB parameter groups. Some variables that were introduced in later MySQL dot releases such as avoid_temporal_upgrade in MySQL 5.6.24 are not made available in RDS's 5.6.x parameter group and making use of them requires an upgrade to MySQL 5.7.x.
-	🔸RDS features such as Point-In-Time restore and snapshot restore are not supported on MyISAM tables. Ensure you lock and flush each MyISAM table before executing a snapshot or backup operation to ensure consistency.

RDS PostgreSQL
--------------
