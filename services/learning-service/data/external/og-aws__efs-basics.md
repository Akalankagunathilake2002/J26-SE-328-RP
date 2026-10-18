<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#efs-basics -->
# AWS Guide: EFS Basics

-	📒 Homepage ∙ User guide ∙ FAQ ∙ Pricing
-	🐥**EFS** is Amazon’s network filesystem. It’s presented as an NFSv4.1 server. Any compatible NFSv4 client can mount it.
-	It is designed to be highly available and durable and each EFS file system object is redundantly stored across multiple availability zones.
-	EFS is designed to be used as a shared network drive and it can automatically scale up to petabytes of stored data and thousands of instances attached to it.
-	EFS can offer higher throughput (multiple gigabytes per second) and better durability and availability than EBS (see the comparison table), but with higher latency.
-	EFS is priced based on the volume of data stored, and costs much more than EBS; it's in the ballpark of three times as much compared to general purpose gp2 EBS volumes.
-	⏱ Performance is dependent on the volume of data stored, as is the price:
	-	Like EBS, EFS uses a credit based system. Credits are earned at a rate of 50 KiB/s per GiB of storage and consumed in bursts during reading/writing files or metadata. Unlike EBS, operations on metadata (file size, owner, date, etc.) also consume credits. The BurstCreditBalance metric in CloudWatch should be monitored to make sure the file system doesn't run out of credits.
	-	Throughput capacity during bursts is also dependent on size. Under 1 TiB, throughput can go up to 100 MiB/s. Above that, 100 MiB/s is added for each stored TiB. For instance, a file system storing 5 TiB would be able to burst at a rate of 500 MiB/s. Maximum throughput per EC2 instance is 250 MiB/s.
	-	EFS has two performance modes that can only be set when a file system is created. One is "General Purpose", the other is "Max I/O". Max I/O scales higher, but at the cost of higher latency. When in doubt, use General Purpose, which is also the default. If the PercentIOLimit metric in CloudWatch hovers around 100%, Max I/O is recommended. Changing performance mode means creating a new EFS and migrating data.
-	High availability is achieved by having mount targets in different subnets / availability zones.

Back to top :arrow_up:
