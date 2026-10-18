<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#cloudfront-tips -->
# AWS Guide: CloudFront Tips

-	🐥**IPv6** is supported. This is a configurable setting, and is enabled by default on new CloudFront distributions. IPv6 support extends to the use of WAF with CloudFront.
-	🐥**HTTP/2** is now supported! Clients must support TLS 1.2 and SNI.
-	While the most common use is for users to browse and download content (GET or HEAD methods) requests, CloudFront also supports (since 2013) uploaded data (POST, PUT, DELETE, OPTIONS, and PATCH).
	-	You must enable this by specifying the allowed HTTP methods when you create the distribution.
	-	Interestingly, the cost of accepting (uploaded) data is usually less than for sending (downloaded) data.
-	In its basic version, CloudFront supports SSL via the SNI extension to TLS, which is supported by all modern web browsers. If you need to support older browsers, you need to pay a few hundred dollars a month for dedicated IPs.
	-	💸⏱Consider invalidation needs carefully. CloudFront does support invalidation of objects from edge locations, but this typically takes many minutes to propagate to edge locations, and costs $0.005 per request after the first 1000 requests. (Some other CDNs support this better.)
-	Everyone should use TLS nowadays if possible. Ilya Grigorik’s table offers a good summary of features regarding TLS performance features of CloudFront.
-	An alternative to invalidation that is often easier to manage, and instant, is to configure the distribution to cache with query strings and then append unique query strings with versions onto assets that are updated frequently.
-	⏱For good web performance, it is recommended to enable compression on CloudFront distributions if the origin is S3 or another source that does not already compress.

Back to top :arrow_up:
