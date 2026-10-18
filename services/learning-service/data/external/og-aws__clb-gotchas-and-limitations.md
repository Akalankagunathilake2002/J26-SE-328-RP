<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#clb-gotchas-and-limitations -->
# AWS Guide: CLB Gotchas and Limitations

-	In general, CLBs are not as “smart” as some load balancers, and don’t have fancy features or fine-grained control a traditional hardware load balancer would offer. For most common cases involving sessionless apps or cookie-based sessions over HTTP, or SSL termination, they work well.
-	🔸By default, CLBs will refuse to route traffic from a load balancer in one Availability Zone (AZ) to a backend instance in another. This will cause 503s if the last instance in an AZ becomes unavailable, even if there are healthy instances in other zones. If you’re running fewer than two backend instances per AZ, you almost certainly want to enable cross-zone load balancing.
-	🔸Complex rules for directing traffic are not supported. For example, you can’t direct traffic based on a regular expression in the URL, like HAProxy offers.
-	**Apex DNS names:** Once upon a time, you couldn’t assign a CLB to an apex DNS record (i.e. example.com instead of foo.example.com) because it needed to be an A record instead of a CNAME. This is now possible with a Route 53 alias record directly pointing to the load balancer.
-	🔸CLBs use HTTP keep-alives on the internal side. This can cause an unexpected side effect: Requests from different clients, each in their own TCP connection on the external side, can end up on the same TCP connection on the internal side. Never assume that multiple requests on the same TCP connection are from the same client!
-	🔸 Traffic between CLBs and back-end instances in the same subnet **will** have Network ACL rules evaluated (EC2 to EC2 traffic in the same subnet would not have Network ACL rules evaluated). If the default '0.0.0.0/0 ALLOW' rule is removed from the Network ACL applied to the subnet, a rule that allows traffic on both the health check port and any listener port must be added.
- As of December 2016, CLBs launched in VPCs do not support IPv6 addressing. CLBs launched in EC2-Classic support both IPv4 and IPv6 with the "dualstack" DNS name.

ALB
---
