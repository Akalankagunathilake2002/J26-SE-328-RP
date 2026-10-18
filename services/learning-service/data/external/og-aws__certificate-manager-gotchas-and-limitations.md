<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#certificate-manager-gotchas-and-limitations -->
# AWS Guide: Certificate Manager Gotchas and Limitations

- 🔸In order to use **Certificate Manager** for CloudFront distributions, the certificate must be issued or imported from us-east-1 (N. Virginia) region.
- 🔸Certificates used with Elastic Load Balancers must be issued in the same region as the load balancer. Certificates can not be moved or copied between regions, as of July 2017. If a domain uses load balancers present in multiple regions, a different certificate must be requested for each region.
- 🔸**IoT** has its own way of setting up certificates.
- 🔸By default the maximum number of domains per certificate is 10. You can get this limit increased to a maximum of 100 by contacting AWS support. **Note** for every different domain you have on the requested cert, you'll need to press accept on an email sent to that domain. For example if you request a cert with 42 different domains or sub domains, you'll need to press accept on 42 different links.
	- 🔹If you request a limit increase to AWS support for this, they will respond to you asking to confirm this. Bypass this by saying in the body of your initial request:
```"I acknowledge at the moment, there is no method to add or remove a name from a certificate. Instead, you must request a new certificate with the revised namelist and you must then re-approve all of the names in the certificate, even if they'd been previously approved."```
- 🔸There is no way at the moment to add or remove a domain to/from an existing certificate. You must request a new certificate and re-approve it from each of the domains requested.

WAF
-------------------
