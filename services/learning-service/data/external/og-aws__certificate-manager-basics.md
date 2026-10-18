<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#certificate-manager-basics -->
# AWS Guide: Certificate Manager Basics

- 📒 Homepage ∙ User guide ∙ FAQ ∙ Pricing
- Use the **Certificate Manager** to manage SSL/TLS certificates in other AWS services.
- Supports importing existing certificates as well as issuing new ones.
- Provides Domain Validated (DV) certificates. Validation can be done in two ways. The first (and recommended) way is via DNS. If the zone lives within Route 53 and the user has access, the necessary record can be added in the console via a single click during the certificate request process. If the zone is not within Route 53 the user is required to update DNS manually. This is still preferred to the second way, which requires more user interaction, and is done by sending an email to 3 contact addresses in WHOIS and 5 common addresses for the domain, for each domain name present in the request.
- ACM will attempt to automatically renew a certificate issued by Amazon. It will first attempt to connect to the domain on HTTPS and check that the certificate used by the domain is the same with the certificate that it intends to renew. Failing that, it will check the DNS record used previously for validation. Failing that, ACM will attempt manual validation by sending emails to all domains in the certificate.

Back to top :arrow_up:
