<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#vpc-and-network-security-tips -->
# AWS Guide: VPC and Network Security Tips

-	❗**Security groups** are your first line of defense for your servers. Be extremely restrictive of what ports are open to all incoming connections. In general, if you use CLBs, ALBs or other load balancing, the only ports that need to be open to incoming traffic would be port 22 and whatever port your application uses. Security groups access policy is 'deny by default'.
-	**Port hygiene:** A good habit is to pick unique ports within an unusual range for each different kind of production service. For example, your web frontend might use 3010, your backend services 3020 and 3021, and your Postgres instances the usual 5432. Then make sure you have fine-grained security groups for each set of servers. This makes you disciplined about listing out your services, but also is more error-proof. For example, should you accidentally have an extra Apache server running on the default port 80 on a backend server, it will not be exposed.
-	**Migrating from Classic**: For migrating from older EC2-Classic deployments to modern EC2-VPC setup, this article may be of help.
	-	You can migrate Elastic IPs between EC2-Classic and EC2-VPC.
-	For basic AWS use, one default VPC may be sufficient. But as you scale up, you should consider mapping out network topology more thoroughly. A good overview of best practices is here.
-	Consider controlling access to you private AWS resources through a VPN.
	-	You get better visibility into and control of connection and connection attempts.
	-	You expose a smaller surface area for attack compared to exposing separate (potentially authenticated) services over the public internet.
		-	e.g. A bug in the YAML parser used by the Ruby on Rails admin site is much less serious when the admin site is only visible to the private network and accessed through VPN.
	-	Another common pattern (especially as deployments get larger, security or regulatory requirements get more stringent, or team sizes increase) is to provide a bastion host behind a VPN through which all SSH connections need to transit.
	-	For a cheap VPN to access private AWS resources, consider using a point-to-site software VPN such as OpenVPN. It can either be installed using the official AMI, though you are limited to 2 concurrent users on the free license, or it can be installed using the openvpn package on linux. The linux package allows for unlimited concurrent users but the installation is less straightforward. This OpenVPN installer script can help you install it and add client keys easily.
-	🔹Consider using other security groups as sources for security group rules instead of using CIDRs — that way, all hosts in the source security group and only hosts in that security group are allowed access. This is a much more dynamic and secure way of managing security group rules.
-	**VPC Flow Logs** allow you to monitor the network traffic to, from, and within your VPC. Logs are stored in CloudWatch Logs groups, and can be used for security monitoring (with third party tools), performance evaluation, and forensic investigation.
	-	See the VPC Flow Logs User Guide for basic information.
	-	See the flowlogs-reader CLI tool and Python library to retrieve and work with VPC Flow Logs.
- **IPv6** is available in VPC. Along with this announcement came the introduction of the Egress-Only Internet Gateway. In cases where one would use NAT Gateways to enable egress-only traffic for their VPC in IPv4, one can use an Egress-Only Internet Gateway for the same purpose in IPv6.

-	Amazon provides an IPv6 CIDR block for your VPC at your request - at present you cannot implement your own IPv6 block if you happen to own one already.
-	New and existing VPCs can both use IPv6. Existing VPCs will need to be configured to have an IPv6 CIDR block associated with them, just as new VPCs do.

Back to top :arrow_up:
