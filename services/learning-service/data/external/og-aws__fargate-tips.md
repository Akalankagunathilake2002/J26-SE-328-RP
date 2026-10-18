<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#fargate-tips -->
# AWS Guide: Fargate Tips

-   Fargate follows a similar mindset to Lambda, which lets you focus on applications, instead of dealing with underlying infrastructure
-   Fargate is supported by CloudFormation, aws-cli and ecs-cli
-   Fargate tasks can be launched alongside tasks that use EC2 Launch Type
-   💸Before creating a large Fargate deployment, make sure to estimate costs and compare them against alternative solution that uses traditional EC2 deployment - Fargate prices can be several times those of equivalently-sized EC2 instances. To evaluate both solutions based on potential costs, refer to pricing for EC2 and Fargate.

Back to top :arrow_up:
