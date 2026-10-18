<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#auto-scaling-tips -->
# AWS Guide: Auto Scaling Tips

-	💸 Better matching your cluster size to your current resource requirements through use of ASGs can result in significant cost savings for many types of workloads.
-	Pairing ASGs with CLBs is a common pattern used to deal with changes in the amount of traffic a service receives.
-	Dynamic Auto Scaling is easiest to use with stateless, horizontally scalable services.
-	Even if you are not using ASGs to dynamically increase or decrease instance counts, you should seriously consider maintaining all instances inside of ASGs – given a target instance count, the ASG will work to ensure that number of instances running is equal to that target, replacing instances for you if they die or are marked as being unhealthy. This results in consistent capacity and better stability for your service.
-	Autoscalers can be configured to terminate instances that a CLB or ALB has marked as being unhealthy.

Back to top :arrow_up:
