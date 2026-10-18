<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#restrictions-and-other-notes -->
# AWS Guide: Restrictions and Other Notes

-	🔸Lots of resources in Amazon have **limits** on them. This is actually helpful, so you don’t incur large costs accidentally. You have to request that quotas be increased by opening support tickets. Some limits are easy to raise, and some are not. (Some of these are noted in sections below.) Additionally, not all service limits are published.
	- **Obtaining Current Limits and Usage:** Limit information for a service may be available from the service API, Trusted Advisor, both or neither (in which case you'll need to contact Support). This page from the awslimitchecker tool's documentation provides a nice summary of available retrieval options for each limit. The tool itself is also valuable for automating limit checks.
-	🔸**AWS terms of service** are extensive. Much is expected boilerplate, but it does contain important notes and restrictions on each service. In particular, there are restrictions against using many AWS services in **safety-critical systems**. (Those appreciative of legal humor may wish to review clause 42.10.)
