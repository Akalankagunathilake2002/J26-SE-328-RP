<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#certificate-manager-tips -->
# AWS Guide: Certificate Manager Tips

- 🔹**Supported services:** Managed Load Balancers, CloudFront, API Gateway and Elastic Beanstalk.
- 🔸During the domain validation process, if DNS validation is unsuccessful Certificate Manager will send an email to every contact address specified in the domain’s WHOIS record and up to five common administrative addresses. Some anti-spam filters can mark emails as spam because of this. You should check the spam folder of your email if you don’t receive a confirmation email.
- 🔹 Setting up a certificate for a test domain you don't have email set up on? You can now use DNS validation instead.
- 🔹Remember when requesting a wildcard domain that the request will not be valid for the level just below the wildcard, or any subdomains preceding the wildcard. Take for example an approved, issued certificate for `*.bar.example.com`. This would be valid for `foo.bar.example.com` but not `bar.example.com`. Likewise it would also not be valid for `www.bar.foo.example.com`. You would need to add each of these domains to the certificate request.

Back to top :arrow_up:
