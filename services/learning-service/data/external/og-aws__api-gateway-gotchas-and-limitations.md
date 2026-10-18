<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#api-gateway-gotchas-and-limitations -->
# AWS Guide: API Gateway Gotchas and Limitations

-	🔸API Gateway only supports encrypted (https) endpoints, and does not support unencrypted HTTP. (This is probably a good thing.)
-	🔸API Gateway doesn’t support multi-region deployments for high availability. It is a service that is deployed in a single region but comes with a global endpoint that is served from AWS edge locations (similar to a CloudFront distribution). You cannot have multiple API Gateways with the same hostname in different AWS regions and use Route 53 to distribute the traffic. More in this forum post.
- 🔸Integration timeout: All of the various integration types (eg: Lambda, HTTP) for API Gateway have timeouts, as described here. Unlike some limits, these timeouts can't be increased.
- 🔸API Gateway returns a 504 status code for any network or low level transport related issue. When this happens, you may see a message in the CloudWatch logs for the request that includes the message: `Execution failed due to an internal error`. One possible reason for this error is that even though your backend server is up and running, it may be doing something outside of the HTTP specification (like not sending well-formed chunked messages). You can test by hitting your backend directly with the `curl --raw -S -i ` and seeing if it complains.
-	🔸AWS X-Ray support exists but cumbersome to use. If you have other AWS services calling API Gateway, your trace will seemingly end there. API Gateway will also not appear as a node in your service map. More here.
-	🔸Be careful using the export feature. The resulting Swagger template is often incomplete and doesn't integrate well with the Swagger extensions for things such as CORS.
-	🔸Many changes to API Gateway resources need to be 'deployed' via console or API call. Unfortunately, API Gateway is terrible about notifying the user when changes are staged for deployment and what changes require deployment. If you've changed something about your API and it's not taking effect, there's a decent chance you just need to deploy it.
	-	In particular, when deploying an API Gateway as part of a CloudFormation stack, changes will not automatically deploy unless the deployment resource itself was changed. You can change work around this by always changing the deployment resource on a CloudFormation update, or running a custom resource that ensures the deployment is made.
	-	Alternatively, by using the Serverless Application Model definition for an API Gateway resource, you can always expect the API to be deployed on a stack update since SAM will generate a new deployment every time.
- 🔸API Gateway does not support nested query parameters on method requests.
- 🔸API Gateway limits number of resources to 300, as described here. This is something to be considered when you start using API Gateway as a platform where your team/organization deploys to the same API Gateway.

🚧 *Please help expand this incomplete section.*

Step Functions
------
