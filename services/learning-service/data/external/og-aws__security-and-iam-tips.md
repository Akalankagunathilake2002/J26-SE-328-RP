<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#security-and-iam-tips -->
# AWS Guide: Security and IAM Tips

-	🔹Use IAM to create individual user accounts and **use IAM accounts for all users from the beginning**. This is slightly more work, but not that much.
	-	That way, you define different users, and groups with different levels of privilege (if you want, choose from Amazon’s default suggestions, of administrator, power user, etc.).
	-	This allows credential revocation, which is critical in some situations. If an employee leaves, or a key is compromised, you can revoke credentials with little effort.
	-	You can set up Active Directory federation to use organizational accounts in AWS.
-	❗**Enable MFA** on your account.
	-	You should always use MFA, and the sooner the better — enabling it when you already have many users is extra work.
	-	Unfortunately it can’t be enforced in software, so an administrative policy has to be established.
	-	Most users can use the Google Authenticator app (on iOS or Android) to support two-factor authentication. For the root account, consider a hardware fob.
- ❗Restrict use of significant IAM credentials as much as possible. Remember that in the cloud, loss of a highly capable IAM credential could essentially mean “game over,” for your deployment, your users, or your whole company.
  -	**Do NOT use the Root User account** other than when you initially create your account.  Create custom IAM users and/or roles and use those for your applications instead.
	- Lock up access and use of the root credentials as much as possible. Ideally they should be effectively “offline.” For critical deployments, this means attached to an actual MFA device, physically secured and rarely used.
-	❗**Turn on CloudTrail:** One of the first things you should do is enable CloudTrail. Even if you are not a security hawk, there is little reason not to do this from the beginning, so you have data on what has been happening in your AWS account should you need that information. You’ll likely also want to set up a log management service to search and access these logs.
-	🔹**Use IAM roles for EC2:** Rather than assign IAM users to applications like services and then sharing the sensitive credentials, define and assign roles to EC2 instances and have applications retrieve credentials from the instance metadata.
-	Assign IAM roles by realm — for example, to development, staging, and production. If you’re setting up a role, it should be tied to a specific realm so you have clean separation. This prevents, for example, a development instance from connecting to a production database.
-	**Best practices:** AWS’ list of best practices is worth reading in full up front.
-	**IAM Reference:** This interactive reference for all IAM actions, effects, and resources is great to have open while writing new or trying to understand existing IAM policies.
-	**Multiple accounts:** Decide on whether you want to use multiple AWS accounts and research how to organize access across them. Factors to consider:
	-	Number of users
	-	Importance of isolation
		-	Resource Limits
		-	Permission granularity
		-	Security
		-	API Limits
	-	Regulatory issues
	-	Workload
	-	Size of infrastructure
	-	Cost of multi-account “overhead”: Internal AWS service management tools may need to be custom built or adapted.
	-	🔹It can help to use separate AWS accounts for independent parts of your infrastructure if you expect a high rate of AWS API calls, since AWS throttles calls at the AWS account level.
-	**Inspector** is an automated security assessment service from AWS that helps identify common security risks. This allows validation that you adhere to certain security practices and may help with compliance.
-	**Trusted Advisor** addresses a variety of best practices, but also offers some basic security checks around IAM usage, security group configurations, and MFA. At paid support tiers, Trusted Advisor exposes additional checks around other areas, such as reserved instance optimization.
-	**Use KMS for managing keys**: AWS offers KMS for securely managing encryption keys, which is usually a far better option than handling key security yourself. See below.
-	**AWS WAF** is a web application firewall to help you protect your applications from common attack patterns.
-	**Security auditing:**
	-	Security Monkey is an open source tool that is designed to assist with security audits.
	-	Scout2 is an open source tool that uses AWS APIs to assess an environment’s security posture. Scout2 is stable and actively maintained.
	-	🔹**Export and audit security settings:** You can audit security policies simply by exporting settings using AWS APIs, e.g. using a Boto script like SecConfig.py (from this 2013 talk) and then reviewing and monitoring changes manually or automatically.

Back to top :arrow_up:
