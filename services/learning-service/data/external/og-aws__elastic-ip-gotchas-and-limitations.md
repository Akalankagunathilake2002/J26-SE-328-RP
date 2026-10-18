<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#elastic-ip-gotchas-and-limitations -->
# AWS Guide: Elastic IP Gotchas and Limitations

-	🔸There is officially no way to allocate a contiguous block of IP addresses, something you may desire when giving IPs to external users. Though when allocating at once, you may get lucky and have some be part of the same CIDR block. If this is important to you, you may want to bring your own IP, which is more involved than this guide will go into.
-	Unofficially, if you have Enterprise support, you can ask your account rep to try to allocate a block of Elastic IPs with a business justification. For example, some of Duo's fixed ranges are blocks of AWS IP space reassigned to `AWS-DUOSECURITYINC`. This is a best effort request, expect a denial.

Glacier
-------
