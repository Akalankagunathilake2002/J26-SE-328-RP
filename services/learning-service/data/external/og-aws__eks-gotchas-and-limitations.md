<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#eks-gotchas-and-limitations -->
# AWS Guide: EKS Gotchas and Limitations

- Pods and Service configurations can rapidly consume IP addresses inside a VPC.  Proper care and maintenance should be applied to ensure IP exhaustion does not occur.
- There is currently no integrated monitoring in CloudWatch for EKS pods or services, you will need to deploy a monitoring system that supports Kubernetes such as Prometheus.
- Autoscaling based off CPU/Memory of a node is limited as you will not be aware of pending Services/Pods that cannot start. Using cluster-autoscaler can be useful for scaling based on Node resource usage and unschedulable Pods.
- Prometheus is a very popular monitoring solution for K8s, metrics and alerts can be used to send events to Lambda, SQS or other solutions to take autoscaling actions.

Back to top :arrow_up:
