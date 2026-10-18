<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#rds-aurora-mysql-basics -->
# AWS Guide: RDS Aurora MySQL Basics

-	Amazon’s proprietary fork of MySQL intended to scale up for high concurrency workloads. Generally speaking, individual query performance under Aurora is not expected to improve significantly relative to MySQL or MariaDB, but Aurora is intended to maintain performance while executing many more queries concurrently than an equivalent MySQL or MariaDB server could handle.
-	Notable new features include:
	-	Log-structured storage instead of B-trees to improve write performance.
	-	Out-of-process buffer pool so that databases instances can be restarted without clearing the buffer pool.
	-	The underlying physical storage is a specialized SSD array that automatically maintains 6 copies of your data across 3 AZs.
	-	Aurora read replicas share the storage layer with the write master which significantly reduces replica lag, eliminates the need for the master to write and distribute the binary log for replication, and allows for zero-data-loss failovers from the master to a replica. The master and all the read replicas that share storage are known collectively as an **Aurora cluster**. Read replicas can span up to 5 regions.

Back to top :arrow_up:
