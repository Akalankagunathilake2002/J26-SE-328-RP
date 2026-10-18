<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#rds-tips -->
# AWS Guide: RDS Tips

-	If you're looking for the managed convenience of RDS for other data stores such as MongoDB or Cassandra, you may wish to consider third-party services from providers such as [Compose, or InstaClustr.
-	🔹Make sure to create a new parameter group and option group for your database since the default parameter group does not allow dynamic configuration changes.
-	RDS instances start with a default timezone of UTC. If necessary, this can be changed to a different timezone.
-	Save costs by stopping the RDS instance(s) when not in use, you can achieve this by configuring a stop and start schedule using the the Instance Scheduler solution.

Back to top :arrow_up:
