<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#billing-and-cost-visibility -->
# AWS Guide: Billing and Cost Visibility

-	AWS offers a **free tier** of service, that allows very limited usage of resources at no cost. For example, a micro instance and small amount of storage is available for no charge. Many services are only eligible for the free tier for the first twelve months that an account exists, but other services offer a free usage tier indefinitely. (If you have an old account but starting fresh, sign up for a new one to qualify for the free tier.) AWS Activate extends this to tens of thousands of dollars of free credits to startups in certain funds or accelerators.
-	You can set **billing alerts** to be notified of unexpected costs, such as costs exceeding the free tier. You can set these in a granular way.
-	AWS offers Cost Explorer, a tool to get better visibility into costs.
-	Unfortunately, the AWS console and billing tools are rarely enough to give good visibility into costs. For large accounts, the AWS billing console can time out or be too slow to use.
-	**Tools:**
	-	🔹Enable billing reports and install an open source tool to help manage or monitor AWS resource utilization. **Teevity Ice** (originally written by Netflix) is probably the first one you should try. Check out docker-ice for a Dockerized version that eases installation.
	-	🔸One challenge with Ice is that it doesn’t cover amortized cost of reserved instances.
	-	Other tools include Security Monkey and Cloud Custodian.
	-	Use AWS Simple Monthly Calculator to get an estimate of usage charges for AWS services based on certain information you provide. Monthly charges will be based on your actual usage of AWS services, and may vary from the estimates the Calculator has provided.
-	**Third-party services:** Several companies offer services designed to help you gain insights into expenses or lower your AWS bill, such as Cloudability, CloudHealth Technologies, and ParkMyCloud. Some of these charge a percentage of your bill, which may be expensive. See the market landscape.
-	AWS’s Trusted Advisor is another service that can help with cost concerns.
-	Don’t be shy about asking your account manager for guidance in reducing your bill. It’s their job to keep you happily using AWS.
-	**Tagging for cost visibility:** As the infrastructure grows, a key part of managing costs is understanding where they lie. It’s strongly advisable to tag resources, and as complexity grows, group them effectively. If you set up billing allocation appropriately, you can then get visibility into expenses according to organization, product, individual engineer, or any other way that is helpful.
-	If you need to do custom analysis of raw billing data or want to feed it to a third party cost analysis service, enable the detailed billing report feature.
-	Multiple Amazon accounts can be linked for billing purposes using the Consolidated Billing feature. Large enterprises may need complex billing structures depending on ownership and approval processes.
-	Multiple Amazon accounts can be managed centrally using AWS Organizations.

Back to top :arrow_up:
