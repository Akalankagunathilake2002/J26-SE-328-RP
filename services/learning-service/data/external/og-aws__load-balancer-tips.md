<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#load-balancer-tips -->
# AWS Guide: Load Balancer Tips

-	If you don’t have opinions on your load balancing up front, and don’t have complex load balancing needs like application-specific routing of requests, it’s reasonable just to use a CLB or ALB for load balancing instead.
-	Even if you don’t want to think about load balancing at all, because your architecture is so simple (say, just one server), put a load balancer in front of it anyway. This gives you more flexibility when upgrading, since you won’t have to change any DNS settings that will be slow to propagate, and also it lets you do a few things like terminate SSL more easily.
-	**CLBs and ALBs have many IPs:** Internally, an AWS load balancer is simply a collection of individual software load balancers hosted within EC2, with DNS load balancing traffic among them. The pool can contain many IPs, at least one per availability zone, and depending on traffic levels. They also support SSL termination, which is very convenient.
-	**Scaling:** CLBs and ALBs can scale to very high throughput, but scaling up is not instantaneous. If you’re expecting to be hit with a lot of traffic suddenly, it can make sense to load test them so they scale up in advance. You can also contact Amazon and have them “pre-warm” the load balancer.
-	**Client IPs:** In general, if servers want to know true client IP addresses, load balancers must forward this information somehow. CLBs add the standard X-Forwarded-For header. When using a CLB as an HTTP load balancer, it’s possible to get the client’s IP address from this.
-	**Using load balancers when deploying:** One common pattern is to swap instances in the load balancer after spinning up a new stack with your latest version, keep old stack running for one or two hours, and either flip back to old stack in case of problems or tear it down.
-   **Rotating Certificates while retaining ARN:** Rotating IAM Server Certificates can be difficult as the standard practice is to upload a new one then update all resources with the new ARN. You can however retain the same ARN using the `update-certificate` call with the following process:
  1. Upload a new IAM Server Certificate with a unique name (e.g fuzzy.com.new)
  2. Rename the existing IAM Server Certificate (e.g fuzzy.com to fuzzy.com.expired)
  3. Rename the new IAM Server Certificate to the name of the previously existing certificate (e.g fuzzy.com.new to fuzzy.com)
  4. Jiggle the CLB/ALB Listener to pick up the change:
      * ALB: Invoke modify-listener with the existing details for the ALB Listener
	  * CLB: Invoke create-load-balancer-listeners with the existing details for the CLB listener

Back to top :arrow_up:
