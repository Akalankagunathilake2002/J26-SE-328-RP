<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#in -->
# AWS Guide: EC2 Alternatives and Lock-In

-	Running EC2 is akin to running a set of physical servers, as long as you don’t do automatic scaling or tooled cluster setup. If you just run a set of static instances, migrating to another VPS or dedicated server provider should not be too hard.
-	🚪**Alternatives to EC2:** The direct alternatives are Google Cloud, Microsoft Azure, Rackspace, DigitalOcean, AWS's own Lightsail offering, and other VPS providers, some of which offer similar APIs for setting up and removing instances. (See the comparisons above.)
-	**Should you use Amazon Linux?** AWS encourages use of their own Amazon Linux, which is evolved from Red Hat Enterprise Linux (RHEL) and CentOS. It’s used by many, but others are skeptical. Whatever you do, think this decision through carefully. It’s true Amazon Linux is heavily tested and better supported in the unlikely event you have deeper issues with OS and virtualization on EC2. But in general, many companies do just fine using a standard, non-Amazon Linux distribution, such as Ubuntu or CentOS. Using a standard Linux distribution means you have an exactly replicable environment should you use another hosting provider instead of (or in addition to) AWS. It’s also helpful if you wish to test deployments on local developer machines running the same standard Linux distribution (a practice that’s getting more common with Docker, too. Amazon now supports an official Amazon Linux Docker image, aimed at assisting with local development on a comparable environment, though this is new enough that it should be considered experimental). Note that the currently-in-testing Amazon Linux 2 supports on-premise deployments explicitly.
-	**EC2 costs:** See the section on this.

Back to top :arrow_up:
