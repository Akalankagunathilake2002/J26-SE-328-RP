<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#auto-scaling-basics -->
# AWS Guide: Auto Scaling Basics

-	📒 Homepage ∙ User guide ∙ FAQ ∙ Pricing at no additional charge
-	**Auto Scaling Groups (ASGs)** are used to control the number of instances in a service, reducing manual effort to provision or deprovision EC2 instances.
-	They can be configured through Scaling Policies to automatically increase or decrease instance counts based on metrics like CPU utilization, or based on a schedule.
-	There are three common ways of using ASGs - dynamic (automatically adjust instance count based on metrics for things like CPU utilization), static (maintain a specific instance count at all times), scheduled (maintain different instance counts at different times of day or on days of the week).
-	💸ASGs have no additional charge themselves; you pay for underlying EC2 and CloudWatch services.

Back to top :arrow_up:
