<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#load-balancer-gotchas-and-limitations -->
# AWS Guide: Load Balancer Gotchas and Limitations

-	❗CLBs and ALBs have **no fixed external IP** that all clients see. For most consumer apps this doesn’t matter, but enterprise customers of yours may want this. IPs will be different for each user, and will vary unpredictably for a single client over time (within the standard EC2 IP ranges). And similarly, never resolve a CLB name to an IP and put it as the value of an A record — it will work for a while, then break!
-	❗Some web clients or reverse proxies cache DNS lookups for a long time, which is problematic for CLBs and ALBs, since they change their IPs. This means after a few minutes, hours, or days, your client will stop working, unless you disable DNS caching. Watch out for Java’s settings and be sure to adjust them properly. Another example is nginx as a reverse proxy, which normally resolves backends only at start-up (although there is a way to get around this).
-	❗It’s not unheard of for IPs to be recycled between customers without a long cool-off period. So as a client, if you cache an IP and are not using SSL (to verify the server), you might get not just errors, but responses from completely different services or companies!
-	🔸As an operator of a service behind a CLB or ALB, the latter phenomenon means you can also see puzzling or erroneous requests by clients of other companies. This is most common with clients using back-end APIs (since web browsers typically cache for a limited period).
-	❗CLBs and ALBs take time to scale up, it does not handle sudden spikes in traffic well. Therefore, if you anticipate a spike, you need to “pre-warm” the load balancer by gradually sending an increasing amount of traffic.
-	❗Tune your healthchecks carefully — if you are too aggressive about deciding when to remove an instance and conservative about adding it back into the pool, the service that your load balancer is fronting may become inaccessible for seconds or minutes at a time. Be extra careful about this when an autoscaler is configured to terminate instances that are marked as being unhealthy by a managed load balancer.
-	❗CLB HTTPS listeners don't support Server Name Indication (SNI). If you need SNI, you can work around this limitation by either providing a certificate with Subject Alternative Names (SANs) or by using TCP listeners and terminating SSL at your backend.
-	🔸 There is a limit on the number of ALBs, CLBs and NLBs per region (separately). As of late 2017, the default limit for each is 20 per region. These limits can be easily raised for ALB and CLB, but AWS is quite reluctant to raise the limit on NLBs.
-	🔸 If using a Network Load Balancer (NLB) then EC2 clients cannot connect to an NLB that resides in another VPC (VPC Peering) or AWS managed VPN unless the EC2 client is a C5, i3.metal or M5 instance type. For VPC peering, both VPCs must be in the same region. See Troubleshooting.

CLB
---
