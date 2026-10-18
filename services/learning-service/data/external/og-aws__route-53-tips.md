<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#route-53-tips -->
# AWS Guide: Route 53 Tips

-	🔹Know about Route 53’s “alias” records:
	-	Route 53 supports all the standard DNS record types, but note that **alias resource record sets** are not standard part of DNS, but a specific Route 53 feature. (It’s available from other DNS providers too, but each provider has a different name for it.)
	-	Aliases are like an internal name (a bit like a CNAME) that is resolved internally on the server side. For example, traditionally you could have a CNAME to the DNS name of a CLB or ALB, but it’s often better to make an alias to the same load balancer. The effect is the same, but in the latter case, externally, all a client sees is the target the record points to.
	-	It’s often wise to use alias record as an alternative to CNAMEs, since they can be updated instantly with an API call, without worrying about DNS propagation.
	-	You can use them for CLBs/ALBs or any other resource where AWS supports it.
	-	Somewhat confusingly, you can have CNAME and A aliases, depending on the type of the target.
	-	Because aliases are extensions to regular DNS records, if exported, the output zone file will have additional non-standard “ALIAS” lines in it.
-	**Latency-based routing** allows users around the globe to be automatically directed to the nearest AWS region where you are running, so that latency is reduced.
-	Understand that domain registration and DNS management (hosted zones) are two separate Route 53 services. When you buy/transfer a domain, Route 53 automatically assigns four name servers to it (e.g. ns-2.awsdns-00.com). Route 53 also offers to automatically create a hosted zone for DNS management, but you are not required do your DNS management in the same account or even in Route 53; you just need to create an NS record pointing to the servers assigned to your domain in Route 53.
  - One use case would be to put your domain registration (very mission critical) in a bastion account while managing the hosted zones within another account which is accessible by your applications.

Back to top :arrow_up:
