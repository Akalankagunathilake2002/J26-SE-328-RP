<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#ec2-cost-management -->
# AWS Guide: EC2 Cost Management

-	With EC2, there is a trade-off between engineering effort (more analysis, more tools, more complex architectures) and spend rate on AWS. If your EC2 costs are small, many of the efforts here are not worth the engineering time required to make them work. But once you know your costs will be growing in excess of an engineer’s salary, serious investment is often worthwhile.
-	Larger instances aren’t necessarily priced higher in the spot market – therefore, you should look at the available options and determine which instances will be most cost effective for your jobs. See Bid Advisor.
-	🔹**Spot instances:**
	-	EC2 Spot instances are a way to get EC2 resources at significant discount — often many times cheaper than standard on-demand prices — if you’re willing to accept the possibility that they be terminated with little to no warning.
	-	Use Spot instances for potentially very significant discounts whenever you can use resources that may be restarted and don’t maintain long-term state.
	-	The huge savings that you can get with Spot come at the cost of a significant increase in complexity when provisioning and reasoning about the availability of compute capacity.
	-	Amazon maintains Spot prices at a market-driven fluctuating level, based on their inventory of unused capacity. Prices are typically low but can spike very high. See the price history to get a sense for this.
	-	You set a bid price high to indicate how high you’re willing to pay, but you only pay the going rate, not the bid rate. If the market rate exceeds the bid, your instance may be terminated.
	-	Prices are per instance type and per availability zone. The same instance type may have wildly different price in different zones at the same time. Different instance types can have very different prices, even for similarly powered instance types in the same zone.
	-	Compare prices across instance types for better deals.
	-	Use Spot instances whenever possible. Setting a high bid price will assure your machines stay up the vast majority of the time, at a fraction of the price of normal instances.
	-	Get notified up to two minutes before price-triggered shutdown by polling your Spot instances’ metadata, or by watching for the termination CloudWatch event.
	-	Make sure your usage profile works well for Spot before investing heavily in tools to manage a particular configuration.
-	**Spot fleet:**
	-	You can realize even bigger cost reductions at the same time as improvements to fleet stability relative to regular Spot usage by using Spot fleet to bid on instances across instance types, availability zones, and (through multiple Spot Fleet Requests) regions.
	-	Spot fleet targets maintaining a specified (and weighted-by-instance-type) total capacity across a cluster of servers. If the Spot price of one instance type and availability zone combination rises above the weighted bid, it will rotate running instances out and bring up new ones of another type and location up in order to maintain the target capacity without going over target cluster cost.
-	**Spot usage best practices:**
	-	**Application profiling:**
		-	Profile your application to figure out its runtime characteristics. That would help give an understanding of the minimum cpu, memory, disk required. Having this information is critical before you try to optimize spot costs.
		-	Once you know the minimum application requirements, instead of resorting to fixed instance types, you can bid across a variety of instance types (that gives you higher chances of getting a spot instance to run your application).E.g., If you know that 4 cpu cores are enough for your job, you can choose any instance type that is equal or above 4 cores and that has the least Spot price based on history. This helps you bid for instances with greater discount (less demand at that point).
	-	**Spot price monitoring and intelligence:**
		-	Spot Instance prices fluctuate depending on instance types, time of day, region and availability zone. The AWS CLI tools and API allow you to describe Spot price metadata given time, instance type, and region/AZ.
		-	Based on history of Spot instance prices, you could potentially build a myriad of algorithms that would help you to pick an instance type in a way that **optimizes cost**, **maximizes availability**, or **offers predictable performance**.
		-	You can also track the number of times an instance of certain type got taken away (out bid) and plot that in graphite to improve your algorithm based on time of day.
	-	**Spot machine resource utilization:**
		-	For running spiky workloads (spark, map reduce jobs) that are schedule based and where failure is non critical, Spot instances become the perfect candidates.
		-	The time it takes to satisfy a Spot instance could vary between 2-10 mins depending on the type of instance and availability of machines in that AZ.
		-	If you are running an infrastructure with hundreds of jobs of spiky nature, it is advisable to start pooling instances to optimize for cost, performance and most importantly time to acquire an instance.
		-	Pooling implies creating and maintaining Spot instances so that they do not get terminated after use. This promotes re-use of Spot instances across jobs. This of course comes with the overhead of lifecycle management.
		-	Pooling has its own set of metrics that can be tracked to optimize resource utilization, efficiency and cost.
		-	Typical pooling implementations give anywhere between 45-60% cost optimizations and 40% reduction in spot instance creation time.
		-	An excellent example of Pooling implementation described by Netflix (part1, part2\)
-	**Spot management gotchas**
	-	🔸**Lifetime:** There is no guarantee for the lifetime of a Spot instance. It is purely based on bidding. If anyone outbids your price, the instance is taken away. Spot is not suitable for time sensitive jobs that have strong SLA. Instances will fail based on demand for Spot at that time. AWS provides a two-minute warning before Amazon EC2 must terminate your Spot instance.
	-	🔹**API return data:** - The Spot price API returns Spot prices of varying granularity depending on the time range specified in the api call.E.g If the last 10 min worth of history is requested, the data is more fine grained. If the last 2 day worth of history is requested, the data is more coarser. Do not assume you will get all the data points. There **will** be skipped intervals.
	-	❗**Lifecycle management:** Do not attempt any fancy Spot management unless absolutely necessary. If your entire usage is only a few machines and your cost is acceptable and your failure rate is lower, do not attempt to optimize. The pain for building/maintaining it is not worth just a few hundred dollar savings.
-	**Reserved Instances:** allow you to get significant discounts on EC2 compute hours in return for a commitment to pay for instance hours of a specific instance type in a specific AWS region and availability zone for a pre-established time frame (1 or 3 years). Further discounts can be realized through “partial” or “all upfront” payment options.
	-	Consider using Reserved Instances when you can predict your longer-term compute needs and need a stronger guarantee of compute availability and continuity than the (typically cheaper) Spot market can provide. However be aware that if your architecture changes your computing needs may change as well so long term contracts can seem attractive but may turn out to be cumbersome.
	-	There are two types of Reserved Instances - Standard and Convertible. If you purchase excess Standard Reserved Instances, you may offer to “sell back” unused Reserved Instances via the Reserved Instance Marketplace, this allows you to potentially recoup the cost of unused EC2 compute instance hours by selling them to other AWS customers.
	-	Instance reservations are not tied to specific EC2 instances - they are applied at the billing level to eligible compute hours as they are consumed across all of the instances in an account.
	-	📜There have been scattered reports of Convertible RI purchases needing to be exercised in a block-- namely, if you buy five convertible RIs in one purchase, you can't convert just two of them. Reach out to your account manager for clarification if this may impact you.
-	If you have multiple AWS accounts and have configured them to roll charges up to one account using the “Consolidated Billing” feature, you can expect *unused* Reserved Instance hours from one account to be applied to matching (region, availability zone, instance type) compute hours from another account.
-	If you have multiple AWS accounts that are linked with Consolidated Billing, plan on using reservations, and want unused reservation capacity to be able to apply to compute hours from other accounts, you’ll need to create your instances in the availability zone with the same *name* across accounts. Keep in mind that when you have done this, your instances may not end up in the same *physical* data center across accounts - Amazon shuffles availability zones names across accounts in order to equalize resource utilization.
-	Make use of dynamic Auto Scaling, where possible, in order to better match your cluster size (and cost) to the current resource requirements of your service.
-	If you use RHEL instances and happen to have existing RHEL on-premise Red Hat subscriptions, then you can leverage Red Hat's Cloud Access program to migrate a portion of your on-premise subscriptions to AWS, and thereby saving on AWS charges for RHEL subscriptions. You can either use your own self-created RHEL AMI's or Red Hat provided Gold Images that will be added to your private AMI's once you sign up for Red Hat Cloud Access.

Further Reading
---------------

This section covers a few unusually useful or “must know about” resources or lists.

-	AWS
	-	AWS In Plain English: A readable overview of all the AWS services.
	-	Awesome AWS: A curated list of AWS tools and software.
	-	AWS Tips I Wish I'd Known Before I Started: A list of tips from Rich Adams
	-	AWS Whitepapers: A list of technical AWS whitepapers, covering topics such as architecture, security and economics.
	-	Last Week in AWS: A weekly email newsletter covering the latest happenings in the AWS ecosystem.
	-	AWS Geek: A blog by AWS Community Hero Jerry Hargrove, with notes and hand-drawn diagrams about various AWS services.
-	Books
	-	Amazon Web Services in Action
	-	AWS Lambda in Action
	-	Serverless Architectures on AWS
	-	Serverless Single Page Apps
	-	The Terraform Book
	-	AWS Scripted 2 book series
	-	Amazon Web Services For Dummies
	-	AWS System Administration
	-	Python and AWS Cookbook
	-	Resilience and Reliability on AWS
	-	AWS documentation as Kindle ebooks
-	General references
	-	AWS Well Architected Framework Guide: Amazon’s own 56 page guide to operational excellence - guidelines and checklists to validate baseline security, reliability, performance (including high availability) and cost optimization practices.
	-	Awesome Microservices: A curated list of tools and technologies for microservice architectures. Worth browsing to learn about popular open source projects.
	-	Is it fast yet?: Ilya Grigorik’s TLS performance overview
	-	High Performance Browser Networking: A full, modern book on web network performance; a presentation on the HTTP/2 portion is here.

Disclaimer
----------

The authors and contributors to this content cannot guarantee the validity of the information found here. Please make sure that you understand that the information provided here is being provided freely, and that no kind of agreement or contract is created between you and any persons associated with this content or project. The authors and contributors do not assume and hereby disclaim any liability to any party for any loss, damage, or disruption caused by errors or omissions in the information contained in, associated with, or linked from this content, whether such errors or omissions result from negligence, accident, or any other cause.

License
-------

[](http://creativecommons.org/licenses/by-sa/4.0/)

This work is licensed under a Creative Commons Attribution-ShareAlike 4.0 International License.
