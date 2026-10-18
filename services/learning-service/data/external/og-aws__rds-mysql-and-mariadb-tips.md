<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#rds-mysql-and-mariadb-tips -->
# AWS Guide: RDS MySQL and MariaDB Tips

-	MySQL RDS allows access to binary logs.
-	Multi-AZ instances of MySQL transparently replicate data across AZs using DRBD. Automated backups of multi-AZ instances run off the backup instance to reduce latency spikes on the primary.
-	🔸**Performance Schema:** While Performance Schema is enabled by default in MySQL 5.6.6 and later, it is disabled by default in all versions of RDS. If you wish to enable Performance Schema, a reboot of the RDS instance will be required.
-	🔸**MySQL vs MariaDB vs Aurora:** If you prefer a MySQL-style database but are starting something new, you probably should consider Aurora and MariaDB as well. **Aurora** has increased availability and is the next-generation solution. That said, Aurora may not be that much faster than MySQL for certain workloads. **MariaDB**, the modern community fork of MySQL, likely now has the edge over MySQL for many purposes and is supported by RDS.

Back to top :arrow_up:
