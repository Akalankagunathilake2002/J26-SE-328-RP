<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#batch-tips -->
# AWS Guide: Batch Tips

- AWS Batch supports prioritization of jobs via the Job Queue Priority. Higher the number - higher the priority.
- AWS Batch supports launching the Compute Environment into specific VPC and subnets.
- A Compute Environment is same as an ECS Cluster.
- There is no additional cost for AWS Batch. You only pay the cost associated with the AWS Services being used - like EC2 Instances and any resources consumed by the batch jobs.
- Associate IAM Roles and policies with the Compute Environment to enable the containers access to other AWS resources.
- 🔹 Use Unmanaged Compute Environments if you need specialized resources like Dedicated Hosts, or EFS.

SQS
-------------------
