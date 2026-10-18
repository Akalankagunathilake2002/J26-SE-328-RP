<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#high-availability-gotchas-and-limitations -->
# AWS Guide: High Availability Gotchas and Limitations

-	🔸**AZ naming** differs from one customer account to the next. Your “us-west-1a” is not the same as another customer’s “us-west-1a” — the letters are assigned to physical AZs randomly per account. This can also be a gotcha if you have multiple AWS accounts. Note that Zone IDs are consistent between accounts, and can be used to reliably align between AWS accounts.
-	🔸💸**Cross-AZ traffic** is not free. At large scale, the costs add up to a significant amount of money. If possible, optimize your traffic to stay within the same AZ as much as possible.

Billing and Cost Management
---------------------------
