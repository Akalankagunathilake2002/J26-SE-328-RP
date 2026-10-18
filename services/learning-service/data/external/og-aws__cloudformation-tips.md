<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#cloudformation-tips -->
# AWS Guide: CloudFormation Tips

-	Validate your stack in a different AWS account! CloudFormation truly shines when making multiple deployments of the same stack to different accounts and regions. A common practice is to deploy stacks in successive stages ending in a production rollout.
-	Avoid potentially time-consuming syntax errors from eating into your deployment time by running `validate-template`.
-	CloudFormation is sometimes slow to update what resources (and new features on old services) a user is able to define in the template. If you need to deploy a resource or feature that isn't supported by the template, CloudFormation allows running arbitrary code (using Lambda) on a stack create or update via custom resources.
-	Custom resources make CloudFormation into a truly powerful tool, as you can do all sorts of neat things quite easily such as sanity tests, initial configuration of Dynamo tables or S3 buckets, cleaning up old CloudWatch logs, etc.
	- For writing Custom Resources in Javascript, AWS provides a good reference in the documentation.
-	CloudFormation offers a visual template designer that can be useful when getting up to speed with the template syntax.
-	By using StackSets, users can define and deploy an entire production application consisting of multiple stacks (one service per stack) in a single CloudFormation template.
-	If you're developing a serverless application (i.e., using Lambda, API Gateway) CloudFormation offers a simplified template format called SAM.
-	❗Use a restrictive stack policy! Without one, you can inadvertently delete live production resources, probably causing a severe outage.
-	❗Turn on termination protection on all of your stacks to avoid costly accidents!
-	The CloudFormation template reference is indispensable when discovering what is and isn't possible in a CloudFormation template.
-	Troposphere is a Python library that makes it much easier to create CloudFormation templates.
	- Currently supports AWS and OpenStack resource types.
	- Troposphere attempts to support all resources types that can be described in CloudFormation templates.
	- Built in error checking.
	- A recommended soft dependency is awacs, which allows you to generate AWS access policy in JSON by writing Python code.
-	stacker is a Python application that makes it easy to define, configure, orchestrate and manage dependencies for CloudFormation stacks across multiple user-defined environments.
-	If you are building different stacks with similar layers, it may be useful to build separate templates for each layer that you can reuse using AWS::CloudFormation::Stack.
-	🔸Avoid hardcoding resource parameters that can potentially change. Use stack parameters as much as you can, and resort to default parameter values.
-	🔹Until 2016, CloudFormation used only an awkward JSON format that makes both reading and debugging difficult. To use it effectively typically involved building additional tooling, including converting it to YAML, but now this is supported directly.
- Wherever possible, export relevant physical IDs from your Stacks by defining Outputs in your CloudFormation Templates. These are the actual names assigned to the resources being created. Outputs can be returned from `DescribeStack` API calls, and get imported to other Stacks as part of the recent addition of cross-stack references.
	-Note that importing outputs in a stack from another stack creates a hard dependency that is tracked by CloudFormation. You will not be able to delete the stack with the outputs until there are no importing stacks.
-	CloudFormation can be set up to send SNS notifications upon state changes, enabling programmatic handling of situations where stacks fail to build, or simple email alerts so the appropriate people are informed.
-	CloudFormation allows the use of **conditionals** when creating a stack.
	-	One common way to leverage this capability is in support of multi-environment CloudFormation templates – by configuring them to use ‘if-else’ statements on the value of a parameter passed in (e.g.  “env”), environment-specific values for things like VPC IDs, SecurityGroup IDs, and AMI names can be passed into reusable generic templates.
-	**Version control your CloudFormation templates!** In the Cloud, an application is the combination of the code written and the infrastructure it runs on. By version controlling **both**, it is easy to roll back to known good states.
-	Avoid naming your resources explicitly (e.g. DynamoDB tables). When deploying multiple stacks to the same AWS account, these names can come into conflict, potentially slowing down your testing. Prefer using resource references instead.
-	For things that shouldn't ever be deleted, you can set an explicit DeletionPolicy on the resource that will prevent the resource from being deleted even if the CloudFormation stack itself is deleted. This is useful for anything that can maintain expensive-to-rebuild state, such as DynamoDB tables, and things that are exposed to the outside world, such as API Gateway APIs.

Back to top :arrow_up:
