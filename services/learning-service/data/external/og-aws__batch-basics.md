<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#batch-basics -->
# AWS Guide: Batch Basics

-	📒 Homepage ∙ Documentation ∙ FAQ ∙ Pricing
- **AWS Batch** is a service that offers an environment to run batch computing jobs. The service dynamically provisions the optimal compute resources needed by the jobs based on their resource requirements, and can scale up to hundreds of thousands of jobs.
- These batch workloads have access to all other AWS services and features.
- AWS Batch, coupled with spot instances can help run the jobs when appropriate capacity is available, providing for optimal utilization of compute resources.
- The batch workloads are built as a Docker Image. These images can then pushed to the EC2 Container Registry (ECR), or any private repository that can be accessed from AWS.
- A Job Definition has the workload's Docker Image URI, and also lets the users specify the environment details like vCPUs, memory, volume mappings, environment variables, parameters, retry strategy, container properties, and the job's IAM role.
- The Compute Environments are EC2 clusters that provide the runtime for the batch workloads to execute in.
- AWS Batch provides managed, as well as unmanaged compute environments. The Managed Environments are provisioned and managed by AWS, while the Unmanaged Environments are managed by the customers.
- The Job Definitions are submitted to Job Queue(s) for execution. Each queue has a priority, and has at least one Compute Environment associated with it.
- AWS Batch uses ECS to execute the containerized jobs.

Back to top :arrow_up:
