<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#aws-data-transfer-costs -->
# AWS Guide: AWS Data Transfer Costs

-	For deployments that involve significant network traffic, a large fraction of AWS expenses are around data transfer. Furthermore, costs of data transfer, within AZs, within regions, between regions, and into and out of AWS and the internet vary significantly depending on deployment choices.
-	Some of the most common gotchas:
	-	🔸*AZ-to-AZ traffic:* Note EC2 traffic between AZs is effectively the same as between regions. For example, deploying a Cassandra cluster across AZs is helpful for high availability, but can hurt on network costs.
	-	🔸*Using public IPs when not necessary:* If you use an Elastic IP or public IP address of an EC2 instance, you will incur network costs, even if it is accessed locally within the AZ.
	-	🔸*Managed NAT Gateway data processing:* Managed NAT Gateways are used to let traffic egress from private subnets--at a cost of 4.5¢ as a data processing fee layered on top of data transfer pricing. Past a certain point, running your own NAT instances becomes far more cost effective.
	-	🔸*Some services do cross-AZ traffic for free:* Many AWS services you'd not consider on their own merits offer a hidden value of free cross-AZ data transfer. EFS, RDS, MSK, and others are examples of this.
-	This figure gives an overview:

Back to top :arrow_up:
