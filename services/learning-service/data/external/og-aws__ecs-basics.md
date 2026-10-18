<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#ecs-basics -->
# AWS Guide: ECS Basics

-	📒 Homepage ∙ Developer guide ∙ FAQ ∙ Pricing
-	**ECS** (EC2 Container Service) is a relatively new service (launched end of 2014) that manages clusters of services deployed via Docker.
-	See the Containers and AWS section for more context on containers.
-	ECS is growing in adoption, especially for companies that embrace microservices.
-	Deploying Docker directly in EC2 yourself is another common approach to using Docker on AWS. Using ECS is not required, and ECS does not (yet) seem to be the predominant way many companies are using Docker on AWS.
-	It’s also possible to use Elastic Beanstalk with Docker, which is reasonable if you’re already using Elastic Beanstalk.
-	Using Docker may change the way your services are deployed within EC2 or Elastic Beanstalk, but it does not radically change how most other services are used.
-	ECR (EC2 Container Registry) is Amazon’s managed Docker registry service. While simpler than running your own registry, it is missing some features that might be desired by some users:
	-	Doesn’t support cross-region replication of images.
		-	If you want fast fleet-wide pulls of large images, you’ll need to push your image into a region-local registry.
	-	Doesn’t support custom domains / certificates.
-	A container’s health is monitored via CLB or ALB. Those can also be used to address a containerized service. When using an ALB you do not need to handle port contention (i.e. services exposing the same port on the same host) since an ALB’s target groups can be associated with ECS-based services directly.
-	The Hitchhikers Guide to AWS ECS and Docker by J. Cole Morrison is an excellent article for Introduction to AWS ECS concepts.

Back to top :arrow_up:
