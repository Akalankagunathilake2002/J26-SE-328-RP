<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#ami-tips -->
# AWS Guide: AMI Tips

-	AMIs are built independently based on how they will be deployed. You must select AMIs that match your deployment when using them or creating them:
	-	EBS or instance store
	-	PV or HVM virtualization types
	-	32 bit (“i386”) vs 64 bit (“amd64”) architecture
-	As discussed above, modern deployments will usually be with **64-bit EBS-backed HVM**.
-	You can create your own custom AMI by snapshotting the state of an EC2 instance that you have modified.
-	AMIs backed by EBS storage have the necessary image data loaded into the EBS volume itself and don’t require an extra pull from S3, which results in EBS-backed instances coming up much faster than instance storage-backed ones.
-	**AMIs are per region**, so you must look up AMIs in your region, or copy your AMIs between regions with the AMI Copy feature.
-	As with other AWS resources, it’s wise to use tags to version AMIs and manage their lifecycle.
-	If you create your own AMIs, there is always some tension in choosing how much installation and configuration you want to “bake” into them.
	-	Baking less into your AMIs (for example, just a configuration management client that downloads, installs, and configures software on new EC2 instances when they are launched) allows you to minimize time spent automating AMI creation and managing the AMI lifecycle (you will likely be able to use fewer AMIs and will probably not need to update them as frequently), but results in longer waits before new instances are ready for use and results in a higher chance of launch-time installation or configuration failures.
	-	Baking more into your AMIs (for example, pre-installing but not fully configuring common software along with a configuration management client that loads configuration settings at launch time) results in a faster launch time and fewer opportunities for your software installation and configuration to break at instance launch time but increases the need for you to create and manage a robust AMI creation pipeline.
	-	Baking even more into your AMIs (for example, installing all required software as well and potentially also environment-specific configuration information) results in fast launch times and a much lower chance of instance launch-time failures but (without additional re-deployment and re-configuration considerations) can require time consuming AMI updates in order to update software or configuration as well as more complex AMI creation automation processes.
-	Which option you favor depends on how quickly you need to scale up capacity, and size and maturity of your team and product.
	-	When instances boot fast, auto-scaled services require less spare capacity built in and can more quickly scale up in response to sudden increases in load. When setting up a service with autoscaling, consider baking more into your AMIs and backing them with the EBS storage option.
	-	As systems become larger, it common to have more complex AMI management, such as a multi-stage AMI creation process in which few (ideally one) common base AMIs are infrequently regenerated when components that are common to all deployed services are updated and then a more frequently run “service-level” AMI generation process that includes installation and possibly configuration of application-specific software.
-	More thinking on AMI creation strategies here.
-	Use tools like Packer to simplify and automate AMI creation.
-	If you use RHEL instances and happen to have existing RHEL on-premise Red Hat subscriptions, then you could leverage Red Hat's Cloud Access program to migrate a portion of your subscriptions to AWS, and thereby not having AWS charge you for RHEL subscriptions a second time. You can either use your own self-created RHEL AMI's or Red Hat provided Gold Images that will be added to your private AMI's once you sign up for Red Hat Cloud Access.

Back to top :arrow_up:
