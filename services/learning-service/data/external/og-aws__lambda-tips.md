<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#lambda-tips -->
# AWS Guide: Lambda Tips

-	The idea behind 'serverless' is that users don't manage provisioning, scaling, or maintenance of the physical machines that host their application code. With Lambda, the machine that actually executes the user-defined function is abstracted as a 'container'. When defining a Lambda function, users are able to declare the amount of memory available to the function, which directly affects the physical hardware specification of the Lambda container.
-	Changing the amount of memory available to your Lambda functions also affects the amount of CPU power available to it.
-	While AWS does not offer hard guarantees around container reuse, in general it can be expected that an unaltered Lambda function will reuse a warm (previously used) container if called shortly after another invocation. Users can use this as a way to optimize their functions by smartly caching application data on initialization.
-	A Lambda that hasn't been invoked in some time may not have any warm containers left. In this case, the Lambda system will have to load and initialize the Lambda code in a 'cold start' scenario, which can add significant latency to Lambda invocations.  Lambda cold start performance has improved significantly over the 2018-2019 timeframe and is now typically in the range of 200-500 ms for a simple function depending on the language runtime.
-	Lambda functions running insides of VPCs have also seen recent improvements to cold start times.  Previously these VPC-hosted functions would have cold starts of ~15 seconds; now those same functions cold start in < 1 second.
-	There are a few strategies to avoiding or mitigating cold starts.  Provisioned concurrency was announced at re:invent 2019 and is an effective means to eliminating cold starts. Other techniques include keeping containers warm by periodic triggering and favoring lightweight runtimes such as Node as opposed to Java.
-	Lambda is integrated with AWS CloudWatch and provides a logger at runtime that publishes CloudWatch events.
-	Lambda offers out-of-the-box opt-in support for AWS X-Ray. X-Ray can help users diagnose Lambda issues by offering in-depth analysis of their Lambda's execution flow. This is especially useful when investigating issues calling other AWS services as X-Ray gives you a detailed and easy-to-parse visualization of the call graph.
-	Using timed CloudWatch events, users can use Lambda to run periodic jobs in a cron-like manner.
-	Events sent to Lambda that fail processing can be managed using a Dead Letter Queue (DLQ) in SQS.
-	More on serverless:
	-	Mike Roberts's thoughts on martinfowler.com.
	-	AWS Serverless Application Model (SAM), a simplification built on top of CloudFormation that can help to define, manage, and deploy serverless applications using Lambda.
	-	Serverless, one of the most popular frameworks for building serverless applications using AWS Lambda and other serverless compute options.
	-	Other helpful frameworks.

Back to top :arrow_up:
