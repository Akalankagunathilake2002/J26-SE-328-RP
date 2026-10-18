<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#cloudfront-gotchas-and-limitations -->
# AWS Guide: CloudFront Gotchas and Limitations

-	🔸If using S3 as a backing store, remember that the endpoints for website hosting and for general S3 are different. Example: “bucketname.s3.amazonaws.com” is a standard S3 serving endpoint, but to have redirect and error page support, you need to use the website hosting endpoint listed for that bucket, e.g. “bucketname.s3-website-us-east-1.amazonaws.com” (or the appropriate region).
-	🔸By default, CloudFront will not forward HTTP Host: headers through to your origin servers. This can be problematic for your origin if you run multiple sites switched with host headers. You can enable host header forwarding in the default cache behavior settings.
-	🔸4096-bit SSL certificates: CloudFront do not support 4096-bit SSL certificates as of late 2016. If you are using an externally issued SSL certificate, you’ll need to make sure it’s 2048 bits. See ongoing discussion.
- Although connections from clients to CloudFront edge servers can make use of IPv6, connections to the origin server will continue to use IPv4.

DirectConnect
-------------
