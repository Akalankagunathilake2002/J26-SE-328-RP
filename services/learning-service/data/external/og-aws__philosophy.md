<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#philosophy -->
# AWS Guide: Philosophy

-	Heroku’s **Twelve-Factor App** principles list some established general best practices for deploying applications.
-	**Pets vs cattle:** Treat servers like cattle, not pets. That is, design systems so infrastructure is disposable. It should be minimally worrisome if a server is unexpectedly destroyed.
-	The concept of **immutable infrastructure** is an extension of this idea.
-	Minimize application state on EC2 instances. In general, instances should be able to be killed or die unexpectedly with minimal impact. State that is in your application should quickly move to RDS, S3, DynamoDB, EFS, or other data stores not on that instance. EBS is also an option, though it generally should not be the bootable volume, and EBS will require manual or automated re-mounting.

Back to top :arrow_up:
