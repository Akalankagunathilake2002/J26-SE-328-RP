<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#common-concepts -->
# AWS Guide: Common Concepts

-	📒 The AWS **General Reference** covers a bunch of common concepts that are relevant for multiple services.
-	AWS allows deployments in **regions**, which are isolated geographic locations that help you reduce latency or offer additional redundancy. Regions contain availability zones(AZs), which are typically the first tool of choice for high availability). AZs are physically separate from one another even within the same region, and may span multiple physical data centers. While they are connected via low latency links, natural disasters afflicting one should not affect others.
-	Each service has API **endpoints** for each region. Endpoints differ from service to service and not all services are available in each region, as listed in these tables.
-	**Amazon Resource Names (ARNs)** are specially formatted identifiers for identifying resources. They start with 'arn:' and are used in many services, and in particular for IAM policies.

Back to top :arrow_up:
