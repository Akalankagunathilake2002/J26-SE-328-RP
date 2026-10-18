<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#cloudformation-gotchas-and-limitations -->
# AWS Guide: CloudFormation Gotchas and Limitations

-	🔸A given CloudFormation stack can end up in a wide variety of states. Error reporting is generally weak, and often times multiple observe-tweak-redeploy cycles are needed to get a working template. The internal state machine for all the varying states is extremely opaque.
-	🔸Some cross-region operations are not possible in CloudFormation without using a custom resource, such as cross-region SNS subscriptions.
-	🔸While having hand-made resources live alongside CloudFormation-created resources is inadvisable, it's sometimes unavoidable. If at all possible, leave ALL resource management up to a CloudFormation template and only provide read-only access to the console.
-	❗Modifications to stack resources made outside CloudFormation can potentially lead to stacks stuck in UPDATE\_ROLLBACK\_FAILED mode. Stacks in this state can be recovered using the continue-update-rollback command. This command can be initiated in the console or in the CLI. The --resources-to-skip parameter usable in the CLI can be useful if the continue-update-rollback command fails. New feature Drift Detection can be used to detect outside changes made to stack.
-	🔸CloudFormation is useful but complex and with a variety of pain points. Many companies find alternate solutions, and many companies use it, but only with significant additional tooling.
-	🔸CloudFormation can be very slow, especially for items like CloudFront distributions and Route53 CNAME entries.
-	🔸It’s hard to assemble good CloudFormation configurations from existing state. AWS does offer a trick to do this, but it’s very clumsy.
	- CloudFormer also hasn't been updated in ages (as of Oct 2017), doesn't support templatizing many new services, and won't fully define even existing services that have since been updated. For example, Dynamo tables defined through CloudFormer won't contain TTL definitions or auto-scaling configuration. There is a third-party version of the tool with more supported resources called Former2.
-	🔸Many users don’t use CloudFormation at all because of its limitations, or because they find other solutions preferable. Often there are other ways to accomplish the same goals, such as local scripts (Boto, Bash, Ansible, etc.) you manage yourself that build infrastructure, or Docker-based solutions (Convox, etc.).
-	🔸Deploying large stacks (i.e., many resources) can be problematic due to unintuitive API limits. For instance, API Gateway's `CreateDeployment` API has a default limit of 3 requests per minute as of 1/12/2018. This limit is readily exceeded even in moderately-sized CloudFormation stacks. Creating CW alarms is another commonly seen limit (`PutMetricAlarm`, 3 tps as of 1/12/2018) especially when creating many autoscaling policies for DynamoDB. One way to work around this limit is to include CloudFormation 'DependsOn' clauses to artificially chain resource creation.
-	🔸Creating/deleting stacks can be a little less clean than ideal. Some resources will leave behind traces in your AWS account even after deletion. E.g., Lambda will leave behind CloudWatch log groups that never expire.

VPCs, Network Security, and Security Groups
-------------------------------------------
