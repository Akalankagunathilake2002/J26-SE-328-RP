<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#vpc-and-network-security-gotchas-and-limitations -->
# AWS Guide: VPC and Network Security Gotchas and Limitations

-	🔸VPCs are tied to one Region in one Account. Subnets are tied to one VPC and limited to one Availability Zone.
-	🔸Security groups are tied to one VPC. If you are utilizing infrastructure in multiple VPCs you should make sure your configuration/deployment tools take that into account.
-	🔸VPC Endpoints are currently only available for S3 and DynamoDB. If you have a security requirement to lockdown outbound traffic from your VPC you may want to use DNS filtering to control outbound traffic to other services.
-	❗Be careful when choosing your VPC IP CIDR block: If you are going to need to make use of ClassicLink, make sure that your private IP range doesn’t overlap with that of EC2 Classic.
-	❗If you are going to peer VPCs, carefully consider the cost of data transfer between VPCs, since for some workloads and integrations, this can be prohibitively expensive.
- ❗New RDS instances require a subnet group within your VPC. If you’re using the default VPC this isn’t a concern, it will contain a subnet for each availability zone in your region. However, if you’re creating your own VPC and plan on using RDS, make sure you have at least two subnets within the VPC to act as the subnet group.
-	❗If you delete the default VPC, you can recreate it via the CLI or the console.
-	❗Be careful with VPC VPN credentials! If lost or compromised, the VPN endpoint must be deleted and recreated. See the instructions for Replacing Compromised Credentials.
-	❗Security Groups and Route Tables apply entries separately for IPv4 and IPv6, so one must ensure they add entries for both protocols accordingly.
- 	💸Managed NAT gateways are a convenient alternative to
manually managing NAT instances, but they do come at a cost per gigabyte. Consider alternatives if you're transferring many terabytes from private subnets to the internet. If you transfer terabytes/petabytes of data from EC2 instances in private subnets to S3, avoid the NAT gateway data processing charge by setting up a Gateway Type VPC Endpoint and route the traffic to/from S3 through the VPC endpoints instead of going through the NAT gateways.

KMS
---
