<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#lambda-code-samples -->
# AWS Guide: Lambda Code Samples

-	Fan-out is an example of using Lambda to “fan-out” or copy data from one service, in this case Kinesis, to multiple other AWS data services. Destinations for fan-out data in the sample include IoT, SQS and more.
-	This AWS limit monitor using Lambdas shows use of multiple Lambdas for monitoring.
-	This Lambda ECS Worker Pattern shows use of Lambda in a workflow where data from S3 is picked up by the Lambda, pushed to a queue, then sent to ECS for more processing.
-	The Secure Pet Store is a sample Java application which uses Lambda and API Gateway with Cognito (for user identity).
-	aws-lambda-list is a list of "hopefully useful AWS lambdas and lambda-related resources". Quite a few code samples here; as usual, not guaranteed tested. Caveat Emptor.

🚧 *Please help expand this incomplete section.*

API Gateway
-----------
