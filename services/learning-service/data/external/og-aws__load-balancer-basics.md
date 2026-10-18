<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#load-balancer-basics -->
# AWS Guide: Load Balancer Basics

-	AWS has 3 load balancing products - “Classic Load Balancers” (CLBs), “Application Load Balancers” (ALBs), and "Network Load Balancers" (NLB).
-	Before the introduction of ALBs, “Classic Load Balancers” were known as “Elastic Load Balancers” (ELBs), so older documentation, tooling, and blog posts may still reference “ELBs”.
-	CLBs have been around since 2009, ALBs in 2016, NLBs were added in 2017 to AWS.
-	CLBs support TCP and HTTP load balancing. ALBs support HTTP load balancing only. NLBs support TCP layer 4 load balancing.
-	CLBs and ALBs can optionally handle termination for a single SSL certificate.
-	All can optionally perform active health checks of instances and remove them from the destination pool if they become unhealthy.
-	CLBs don't support complex / rule-based routing. ALBs support a (currently small) set of rule-based routing features. NLBs have most extensive routing options.
-	CLBs can only forward traffic to a single globally configured port on destination instances, while ALBs can forward to ports that are configured on a per-instance basis, better supporting routing to services on shared clusters with dynamic port assignment (like ECS or Mesos). NLBs support multiple ports on same IP; registering targets by IP address, including targets outside the VPC for the load balancer; ECS can select unused port for scheduling a task then register a target group using this port.
-	CLBs are supported in EC2 Classic as well as in VPCs while ALBs are supported in VPCs only.
-   ALBs can target groups of instances and IP based targets in the RFC1918 ranges allowing you to use on premise destinations via VPN or Direct Connect.

Back to top :arrow_up:
