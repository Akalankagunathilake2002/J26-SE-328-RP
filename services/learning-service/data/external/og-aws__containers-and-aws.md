<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#containers-and-aws -->
# AWS Guide: Containers and AWS

-	Docker and the containerization trend are changing the way many servers and services are deployed in general.
-	Containers are designed as a way to package up your application(s) and all of their dependencies in a known way. When you build a container, you are including every library or binary your application needs, outside of the kernel. A big advantage of this approach is that it’s easy to test and validate a container locally without worrying about some difference between your computer and the servers you deploy on.
-	A consequence of this is that you need fewer AMIs and boot scripts; for most deployments, the only boot script you need is a template that fetches an exported docker image and runs it.
-	Companies that are embracing microservice architectures will often turn to container-based deployments.
-	AWS launched ECS as a service to manage clusters via Docker in late 2014, though many people still deploy Docker directly themselves. See the ECS section for more details.
-	AWS launched EKS as a service to manage Kubernetes Clusters mid 2018, though many people still deploy ECS or use Docker directly themselves. See the EKS section for more details.

Back to top :arrow_up:
