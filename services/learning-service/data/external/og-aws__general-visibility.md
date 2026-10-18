<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#general-visibility -->
# AWS Guide: General Visibility

-	🔹**Tagging resources** is an essential practice, especially as organizations grow, to better understand your resource usage. For example, through automation or convention, you can add tags:
	-	For the org or developer that “owns” that resource
	-	For the product that resource supports
	-	To label lifecycles, such as temporary resources or one that should be deprovisioned in the future
	-	To distinguish production-critical infrastructure (e.g. serving systems vs backend pipelines)
	-	To distinguish resources with special security or compliance requirements
	-	To (once enabled) allocate cost. Note that cost allocation tags only apply on a forward-looking basis; you can't retroactively apply them to items already billed.
	-	For many years, there was a notorious 10 tag limit per resource, which could not be raised and caused many companies significant pain. As of 2016, this was raised to 50 tags per resource.
	-	🔹In 2017, AWS introduced the ability to enforce tagging on instance and volume creation, deprecating portions of third party tools such as Cloud Custodian.
	-	🔸 Tags are case sensitive; 'environment' and 'Environment' are two different tags. Automation in setting tags is likely the only sensible option at significant scale.
	-	🔸 There is a bug in the ASG console where spaces after tag names are preserved. So if you type "Name " with a space at the end you will not get the expected behavior. This is probably true in other locations and SDKs also. Be sure you do not add trailing spaces to tag keys unless you really mean it. (As of Jul 2018)
	-	🔸 When resources are shared across the org, tags are not shared with it. For example, sharing Transit Gateway or AMIs will show the correct tags in the account that created these resources but not in the accounts where these resources were shared.

Managing Servers and Applications
---------------------------------

Back to top :arrow_up:
