<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#elastic-ip-tips -->
# AWS Guide: Elastic IP Tips

-	🔹**Prefer load balancers to elastic IPs:** For single-instance deployments, you could just assign elastic IP to an instance, give that IP a DNS name, and consider that your deployment. Most of the time, you should provision a load balancer instead:
	-	It’s easy to add and remove instances from load balancers. It’s also quicker to add or remove instances from a load balancer than to reassign an elastic IP.
	-	It’s more convenient to point DNS records to load balancers, instead of pointing them to specific IPs you manage manually. They can also be Route 53 aliases, which are easier to change and manage.
	-	But in some situations, you do need to manage and fix IP addresses of EC2 instances, for example if a customer needs a fixed IP. These situations require elastic IPs.
-	Elastic IPs are limited to 5 per account. It’s possible to request more.
-	If an Elastic IP is not attached to an active resource there is a small hourly fee.
-	Elastic IPs are no extra charge as long as you’re using them. They have a (small) cost when not in use, which is a mechanism to prevent people from squatting on excessive numbers of IP addresses.

Back to top :arrow_up:
