<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#efs-gotchas-and-limitations -->
# AWS Guide: EFS Gotchas and Limitations

-	🔸 A number of NFSv4.1 features are not supported and there are some limits to the service.
-	🔸 As of 2017-08, EFS offers disk level encryption for new drives. For file systems created before that date, encryption can only be achieved by moving the data to a new EFS volume.
-	🔸 An EFS file system can be mounted on premises over Direct Connect.
-	🔸 An EFS file system can NOT be mounted over VPC peering or VPN, even if the VPN is running on top of Direct Connect.
-	🔸 Using an EFS volume on Windows is not supported.
-	⏱ When a file is uploaded to EFS, it can take hours for EFS to update the details for billing and burst credit purposes.
-	🔸⏱  Metadata operations can be costly in terms of burst credit consumption. Recursively traversing a tree containing thousands of files can easily ramp up to tens or even hundreds of megabytes of burst credits being consumed, even if no file is being touched. Commands like ```find``` or ```chown -R``` can have an adverse impact on performance.

Load Balancers
--------------
