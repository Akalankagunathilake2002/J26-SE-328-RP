<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#aws-console -->
# AWS Guide: AWS Console

-	The AWS Console lets you control much (but not all) functionality of AWS via a web interface.
-	Ideally, you should only use the AWS Console in a few specific situations:
	-	It’s great for read-only usage. If you’re trying to understand the state of your system, logging in and browsing it is very helpful.
	-	It is also reasonably workable for very small systems and teams (for example, one engineer setting up one server that doesn’t change often).
	-	It can be useful for operations you’re only going to do rarely, like less than once a month (for example, a one-time VPC setup you probably won’t revisit for a year). In this case using the console can be the simplest approach.
-	❗**Think before you use the console:** The AWS Console is convenient, but also the enemy of automation, reproducibility, and team communication. If you’re likely to be making the same change multiple times, avoid the console. Favor some sort of automation, or at least have a path toward automation, as discussed next. Not only does using the console preclude automation, which wastes time later, but it prevents documentation, clarity, and standardization around processes for yourself and your team.
