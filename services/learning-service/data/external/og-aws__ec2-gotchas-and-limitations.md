<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#ec2-gotchas-and-limitations -->
# AWS Guide: EC2 Gotchas and Limitations

-	❗Never use ssh passwords. Just don’t do it; they are too insecure, and consequences of compromise too severe. Use keys instead. Read up on this and fully disable ssh password access to your ssh server by making sure 'PasswordAuthentication no' is in your /etc/ssh/sshd_config file. If you’re careful about managing ssh private keys everywhere they are stored, it is a major improvement on security over password-based authentication.
-	🔸For all newer instance types, when selecting the AMI to use, be sure you select the HVM AMI, or it just won’t work.
-	❗When creating an instance and using a new ssh key pair, make sure the ssh key permissions are correct.
-	🔸Sometimes certain EC2 instances can get scheduled for retirement by AWS due to “detected degradation of the underlying hardware,” in which case you are given a couple of weeks to migrate to a new instance
 	-	If your instance root device is an EBS volume, you can typically stop and then start the instance which moves it to healthy host hardware, giving you control over timing of this event. Note however that you will lose any instance store volume data (ephemeral drives) if your instance type has instance store volumes.
 	-	The instance public IP (if it has one) will likely change unless you're using Elastic IPs. This could be a problem if other systems depend on the IP address.
-	🔸Periodically you may find that your server or load balancer is receiving traffic for (presumably) a previous EC2 server that was running at the same IP address that you are handed out now (this may not matter, or it can be fixed by migrating to another new instance).
-	❗If the EC2 API itself is a critical dependency of your infrastructure (e.g. for automated server replacement, custom scaling algorithms, etc.) and you are running at a large scale or making many EC2 API calls, make sure that you understand when they might fail (calls to it are rate limited and the limits are not published and subject to change) and code and test against that possibility.
-	❗Many newer EC2 instance types are either EBS-only, or backed by local NVMe disks assigned to the instance. Make sure to factor in EBS performance and costs when planning to use them.
-	❗If you're operating at significant scale, you may wish to break apart API calls that enumerate all of your resources, and instead operate either on individual resources, or a subset of the entire list. EC2 APIs will time out! Consider using filters to restrict what gets returned.
-	❗⏱ Instances come in two types: **Fixed Performance Instances** (e.g. M3, C3, and R3) and **Burstable Performance Instances** (e.g. T2). A T2 instance receives CPU credits continuously, the rate of which depends on the instance size. T2 instances accrue CPU credits when they are idle, and use CPU credits when they are active. However, once an instance runs out of credits, you'll notice a severe degradation in performance. If you need consistently high CPU performance for applications such as video encoding, high volume websites or HPC applications, it is recommended to use Fixed Performance Instances.
-	Instance user-data is limited to 16 KB. (This limit applies to the data in raw form, not base64-encoded form.) If more data is needed, it can be downloaded from S3 by a user-data script.
-	Very new accounts may not be able to launch some instance types, such as GPU instances, because of an initially imposed “soft limit” of zero. This limit can be raised by making a support request. See AWS Service Limits for the method to make the support request. Note that this limit of zero is not currently documented.
- Since multiple AWS instances all run on the same physical hardware, early cloud adopters encountered what became known as the Noisy Neighbor problem. This feeling of not getting what you are paying for led to user frustration, however "steal" may not be the best word to describe what's actually happening based on a detailed explanation of how the kernel determine steal time. Avoiding having CPU steal affect your application in the cloud may be best handled by properly designing your cloud architecture.
- AWS introduced Dedicated Tenancy in 2011. This allows customers to have all resources from a single server. Some saw this as a way to solve the noisy neighbor problem since only that customer uses the CPU. This approach comes with a significant risk if that physical system needed any type of maintenance. If a customer had 20 instances running using shared tenancy and one underlying server needed maintenance, only the instance on that server would go offline. If that customer had 20 instances running using dedicated tenancy, when the underlying server needs maintenance, all 20 instances would go offline.
-	🔸Only **i3.metal** type instances providing an ability to run Android x86 emulators on AWS at the moment.

CloudWatch
-------------------
