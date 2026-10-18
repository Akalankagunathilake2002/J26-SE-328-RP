<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#lambda-gotchas-and-limitations -->
# AWS Guide: Lambda Gotchas and Limitations

- 🔸Testing Lambdas, locally and remotely, can be a challenge. Several tools are available to make this easier, including the officially supported SAM Local.
- 🔸Managing lots of Lambda functions is a workflow challenge, and tooling to manage Lambda deployments is still immature.
- 🔸AWS’ official workflow around managing function versioning and aliases is painful. One option is to avoid Lambda versioning by abstracting your deployment workflow outside of Lambda. One way this can be accomplished is by deploying your application in successive stages, with a distinct AWS account per stage, where each account only needs to be aware of the latest version, and rollbacks and updates are handled by external tooling.
- 🔸While adding/removing S3 buckets as triggers for Lambda function, this error may occur: "There was an error creating the trigger: Configuration is ambiguously defined. Cannot have overlapping suffixes in two rules if the prefixes are overlapping for the same event type." In this case, you can manually remove the Lambda event in the "Events" tab in the "Properties" section of the S3 bucket.
- 🔸Managing the size of your deployment artifact can be a challenge, especially if using Java. Options to mitigate this include proguard and loading dependencies at runtime into /tmp.
- When using DynamoDB as a trigger for your Lambda functions, this error may occur: "PROBLEM: internal Lambda error. Please contact Lambda customer support." This usually just means that Lambda can't detect anything in the DynamoDB stream within the last 48 hours. If the issue persists, deleting and recreating your trigger may help.
- 🔸If your lambda needs access to resources in a VPC (for example ElastiCache or RDS), it will need to be deployed within it. This will increase cold-start times as an Elastic Network Interface (ENI) will have to be registered within the VPC for each concurrent function. AWS also has a relatively low initial limit (350) on the number ENI's that can be created within an VPC, however this can be increased to the 1000s if a good case is made to AWS support.
- 🔸If your lambda is in a VPC and needs access to resources outside VPC such outbound internet access, it will need a NAT gateway associated even if it is in public subnet. Lambdas won't be assigned a public IP irrespective of subnet. If it is accessing AWS services (for example S3), you may use VPC endpoints.
-	🔸 Lambda has several **resource limits** as of 2017-06:
	-	A **6MB** request or response payload size.
	-	A **50 MB** limit on the compressed .zip/.jar file deployment package size.
	-	A **250 MB** limit on the code/dependencies in the package before compression.
	- A **500 MB** limit on local storage in /tmp.

Back to top :arrow_up:
