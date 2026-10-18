<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#security-and-iam-basics -->
# AWS Guide: Security and IAM Basics

-	📒 IAM Homepage ∙ User guide ∙ FAQ
-	The AWS Security Blog is one of the best sources of news and information on AWS security.
-	**IAM** is the service you use to manage accounts and permissioning for AWS.
-	Managing security and access control with AWS is critical, so every AWS administrator needs to use and understand IAM, at least at a basic level.
-	IAM identities include users (people or services that are using AWS), groups (containers for sets of users and their permissions), and roles (containers for permissions assigned to AWS service instances). Permissions for these identities are governed by policies You can use AWS pre-defined policies or custom policies that you create.
-	IAM manages various kinds of authentication, for both users and for software services that may need to authenticate with AWS, including:
	-	**Passwords** to log into the console. These are a username and password for real users.
	-	**Access keys**, which you may use with command-line tools. These are two strings, one the “id”, which is an upper-case alphabetic string of the form 'AXXXXXXXXXXXXXXXXXXX', and the other is the secret, which is a 40-character mixed-case base64-style string. These are often set up for services, not just users.
		-	📜 Access keys that start with AKIA are normal keys. Access keys that start with ASIA are session/temporary keys from STS, and will require an additional "SessionToken" parameter to be sent along with the id and secret. See the documentation for a complete list of access key prefixes.
	-	**Multi-factor authentication (MFA)**, which is the highly recommended practice of using a keychain fob or smartphone app as a second layer of protection for user authentication.
-	IAM allows complex and fine-grained control of permissions, dividing users into groups, assigning permissions to roles, and so on. There is a policy language that can be used to customize security policies in a fine-grained way.
	-	An excellent high level overview of IAM policy concepts lives at IAM Policies In A Nutshell.
	-	🔸The policy language has a complex and error-prone JSON syntax that’s quite confusing, so unless you are an expert, it is wise to base yours off trusted examples or AWS’ own pre-defined managed policies.
-	At the beginning, IAM policy may be very simple, but for large systems, it will grow in complexity, and need to be managed with care.
	-	🔹Make sure one person (perhaps with a backup) in your organization is formally assigned ownership of managing IAM policies, make sure every administrator works with that person to have changes reviewed. This goes a long way to avoiding accidental and serious misconfigurations.
-	It is best to give each user or service the minimum privileges needed to perform their duties. This is the principle of least privilege, one of the foundations of good security. Organize all IAM users and groups according to levels of access they need.
-	IAM has the permission hierarchy of:
	1. Explicit deny: The most restrictive policy wins.
	2. Explicit allow: Access permissions to any resource has to be explicitly given.
	3. Implicit deny: All permissions are implicitly denied by default.
-	You can test policy permissions via the AWS IAM policy simulator tool. This is particularly useful if you write custom policies.

Back to top :arrow_up:
