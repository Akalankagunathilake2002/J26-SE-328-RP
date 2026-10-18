<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#ecs-tips -->
# AWS Guide: ECS Tips

-	**Log drivers:** ECS supports multiple log drivers (awslogs, splunk, fluentd, syslog, json, ... ). Use `awslogs` for CloudWatch (make sure a group is made for the logs first). Drivers such as fluentd are not enabled by default. You can, install the agent and enable the driver by adding `ECS_AVAILABLE_LOGGING_DRIVERS='["awslogs","fluentd"]'` to `/etc/ecs/ecs.config`.
-	This blog from Convox (and commentary) lists a number of common challenges with ECS as of early 2016.
- It is possible to optimize disk clean up on ECS. By default, the unused containers are deleted after 3 hours and the unused images after 30 minutes. These settings can be changed by adding `ECS_ENGINE_TASK_CLEANUP_WAIT_DURATION=10m` and `ECS_IMAGE_CLEANUP_INTERVAL=10m` to `/etc/ecs/ecs.config`. More information on optimizing ECS disk cleanup.

Back to top :arrow_up:
