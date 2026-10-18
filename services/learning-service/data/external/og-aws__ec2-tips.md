<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#ec2-tips -->
# AWS Guide: EC2 Tips

-	🔹**Picking regions:** When you first set up, consider which regions you want to use first. Many people in North America just automatically set up in the us-east-1 (N. Virginia) region, which is the default, but it’s worth considering if this is best up front. You'll want to evaluate service availability (some services are not available in all regions), costing (baseline costs also vary by region by up to 10-30% (generally lowest in us-east-1 for comparison purposes)), and compliance (various countries have differing regulations with regard to data privacy, for example).
-	**Instance types:** EC2 instances come in many types, corresponding to the capabilities of the virtual machine in CPU architecture and speed, RAM, disk sizes and types (SSD or magnetic), and network bandwidth.
	-	Selecting instance types is complex since there are so many types. Additionally there are different generations, released over the years.
	-	🔹Use the list at **ec2instances.info** to review costs and features. Amazon’s own list of instance types is hard to use, and doesn’t list features and price together, which makes it doubly difficult.
	-	Prices vary a lot, so use **ec2instances.info** to determine the set of machines that meet your needs and **ec2price.com** to find the cheapest type in the region you’re working in. Depending on the timing and region, it might be much cheaper to rent an instance with *more* memory or CPU than the bare minimum.
  - **Turn off** your instances when they aren’t in use. For many situations such as testing or staging resources, you may not need your instances on 24/7, and you won’t need to pay EC2 running costs when they are suspended. Given that costs are calculated based on usage, this is a simple mechanism for cost savings. This can be achieved using Lambda and CloudWatch, deploying the Instance Scheduler solution, an open source option like cloudcycler, or a SaaS provider like GorillaStack. (Note: if you turn off instances with an ephemeral root volume, any state will be lost when the instance is turned off. Therefore, for stateful applications it is safer to turn off EBS backed instances).
-	**Dedicated instances** and **dedicated hosts** are assigned hardware, instead of usual virtual instances. They are more expensive than virtual instances but can be preferable for performance, compliance, financial modeling, or licensing reasons.
-	**32 bit vs 64 bit:** A few micro, small, and medium instances are still available to use as 32-bit architecture. You’ll be using 64-bit EC2 (“amd64”) instances nowadays, though smaller instances still support 32 bit (“i386”). Use 64 bit unless you have legacy constraints or other good reasons to use 32.
-	**HVM vs PV:** There are two kinds of virtualization technology used by EC2, hardware virtual machine (HVM) and paravirtual (PV). Historically, PV was the usual type, but now HVM is becoming the standard. If you want to use the newest instance types, you must use HVM. See the instance type matrix for details.
-	**Operating system:** To use EC2, you’ll need to pick a base operating system. It can be Windows or Linux, such as Ubuntu or Amazon Linux. You do this with AMIs, which are covered in more detail in their own section below.
-	**Limits:** You can’t create arbitrary numbers of instances. Default limits on numbers of EC2 instances per account vary by instance type, as described in this list.
-	❗**Use termination protection:** For any instances that are important and long-lived (in particular, aren't part of auto-scaling), enable termination protection. This is an important line of defense against user mistakes, such as accidentally terminating many instances instead of just one due to human error.
-	**SSH key management:**
	-	When you start an instance, you need to have at least one ssh key pair set up, to bootstrap, i.e., allow you to ssh in the first time.
	-	Aside from bootstrapping, you should manage keys yourself on the instances, assigning individual keys to individual users or services as appropriate.
	-	Avoid reusing the original boot keys except by administrators when creating new instances.
	-	Avoid sharing keys and add individual ssh keys for individual users.
-	**GPU support:** You can rent GPU-enabled instances on EC2 for use in machine learning or graphics rendering workloads.

	-	There are three types of GPU-enabled instances currently available:
		- The P3 series offers NVIDIA Tesla V100 GPUs in 1, 4 and 8 GPU configurations targeting machine learning, scientific workloads, and other high performance computing applications.
		- The P2 series offers NVIDIA Tesla K80 GPUs in 1, 8 and 16 GPU configurations targeting machine learning, scientific workloads, and other high performance computing applications.
		- The G3 series offers NVIDIA Tesla M60 GPUs in 1, 2, or 4 GPU configurations targeting graphics and video encoding.
	-	AWS offers two different AMIs that are targeted to GPU applications. In particular, they target deep learning workloads, but also provide access to more stripped-down driver-only base images.
		-	AWS offers both an Amazon Linux Deep Learning AMI (based on Amazon Linux) as well as an Ubuntu Deep Learning AMI. Both come with most NVIDIA drivers and ancillary software (CUDA, CUBLAS, CuDNN, TensorFlow, PyTorch, etc.) installed to lower the barrier to usage.
		-	⛓ Note that using these AMIs can lead to lock in due to the fact that you have no direct access to software configuration or versioning.
		-	🔸 The compendium of frameworks included can lead to long instance startup times and difficult-to-reason-about environments.
	-	🔹As with any expensive EC2 instance types, Spot instances can offer significant savings with GPU workloads when interruptions are tolerable.
- All current EC2 instance types can take advantage of IPv6 addressing, so long as they are launched in a subnet with an allocated CIDR range in an IPv6-enabled VPC.

Back to top :arrow_up:
