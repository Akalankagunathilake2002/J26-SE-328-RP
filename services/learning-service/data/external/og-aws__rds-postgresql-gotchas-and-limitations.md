<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#rds-postgresql-gotchas-and-limitations -->
# AWS Guide: RDS PostgreSQL Gotchas and Limitations

- No superuser privileges. RDS provides a role `rds_superuser` that can do most of the needed operations but there are some limitations.
- Some major features are delayed compared to open source PostgreSQL.
- By default RDS is spec’d with general purpose SSD , if you need better performance you have to spec provisioned IOPS SSD.
- You can't use RDS as a replica outside RDS without using logical replication.
- There are settings that cannot be changed and most of the settings that can change can only be changed using database parameter groups.
- It’s harder to troubleshoot performance problems since you have no access to the host.
- Be sure to verify that all the extensions you need are available. If you are using an extension not listed there, you will need to come up with a work around, or deploy your own database in EC2.
- Many Postgres utilities and maintenance items expect command line access, that can usually be satisfied by using an external ec2 server.

RDS SQL Server
--------------
