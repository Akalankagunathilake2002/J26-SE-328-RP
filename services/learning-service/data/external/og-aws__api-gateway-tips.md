<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#api-gateway-tips -->
# AWS Guide: API Gateway Tips

-	🔹Prior to 2016-11, you could only send and receive plain text data (so people would base64-encode binary data), but binary data is now supported.
-	API Gateway supports the OpenApi specification (aka Swagger). This allows you to describe your API in a language-agnostic way and use various tools to generate code supporting your API.
-	Generating clients is extremely easy, either through the AWS console or using the get-sdk API.
-	API Gateway integrates with CloudWatch out-of-the-box, allowing for easy logging of requests and responses.
	-	Note that if your request or response are too large, CloudWatch will truncate the log. For full request/reply logging, make sure to do so in your integration (e.g. Lambda).
	-	A good practice when calling API Gateway APIs is to log the request ID on the client. You can later refer to these request IDs in CloudWatch for easier tracing and debugging.
-	There are multiple ways to secure your API, including built-in support for AWS Cognito. For most use-cases, Cognito is the easiest and simplest way to authenticate users.
	-	Although you can roll your own solution using a custom authorizer, which is basically a Lambda you define that determines if a request is acceptable or not.
-	While API Gateway lends itself well to REST-style development, it's perfectly reasonable to implement an RPC-style API in API Gateway as well. Depending on your use-case, this can often lead to a much simpler API structure and smoother client experience.
	-	RPC-style APIs are particularly useful when designing services that sit deeper in the stack and don't serve content directly to users.

Back to top :arrow_up:
