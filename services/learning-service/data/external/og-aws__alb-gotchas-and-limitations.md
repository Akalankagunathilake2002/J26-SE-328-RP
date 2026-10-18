<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#alb-gotchas-and-limitations -->
# AWS Guide: ALB Gotchas and Limitations

-	🔸ALBs only support HTTP/2 over HTTPS (no plain-text HTTP/2).
-	🔸ALBs only support HTTP/2 to external clients and not to internal resources (instances/containers).
-	ALBs support HTTP routing but not port-based TCP routing.
-	Instances in the ALB’s target groups have to either have a single, fixed healthcheck port (“EC2 instance”-level healthcheck) or the healthcheck port for a target has to be the same as its application port (“Application instance”-level healthcheck) - you can't configure a per-target healthcheck port that is different than the application port.
-	ALBs are VPC-only (they are not available in EC2 Classic)
-	In a target group, if there is no healthy target, all requests are routed to all targets. For example, if you point a listener at a target group containing a single service that has a long initialization phase (during which the health checks would fail), requests will reach the service while it is still starting up.
- 📜 Although ALBs now support SNI, they only support 25 HTTPS certificates per Load Balancer. This limitation is not described here, so it might be subject to change.

Elastic Beanstalk
----------------
