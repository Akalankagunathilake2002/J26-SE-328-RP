<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#boto -->
# AWS Guide: Boto

-	A good way to automate operations in a custom way is **Boto3**, also known as the Amazon SDK for Python. **Boto2**, the previous version of this library, has been in wide use for years, but now there is a newer version with official support from Amazon, so prefer Boto3 for new projects.
-	Boto3 contains a variety of APIs that operate at either a high level or a low level, here some explanation of both:
	-	The low level APIs (Client APIs) are mapped to AWS Cloud service-specific APIs, and all service operations are supported by clients. Clients are generated from a JSON service definition file.
	-	The high level option, Resource APIs, allows you to avoid calling the network at the low level and instead provide an object-oriented way to interact with AWS Cloud services.
-	Boto3 has a lot of helpful **features** like *waiters*, which provide a structure that allows for code to wait for changes to occur in the cloud, for example, when you are creating an EC2 instance and need wait until the instance is running in order to perform another task.
-	If you find yourself writing a Bash script with more than one or two CLI commands, you’re probably doing it wrong. Stop, and consider writing a Boto script instead. This has the advantages that you can:
	-	Check return codes easily so success of each step depends on success of past steps.
	-	Grab interesting bits of data from responses, like instance ids or DNS names.
	-	Add useful environment information (for example, tag your instances with git revisions, or inject the latest build identifier into your initialization script).

Back to top :arrow_up:
