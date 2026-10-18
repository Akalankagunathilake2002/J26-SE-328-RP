<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#ec2-basics -->
# AWS Guide: EC2 Basics

-	📒 Homepage ∙ Documentation ∙ FAQ ∙ Pricing (see also ec2instances.info\)
-	**EC2** (Elastic Compute Cloud) is AWS’ offering of the most fundamental piece of cloud computing: A virtual private server. These “instances” can run most Linux, BSD, and Windows operating systems. Internally, they've used a heavily modified Xen virtualization. That said, new instance classes are being introduced with a KVM derived hypervisor instead, called Nitro. So far, this is limited to the C5 and M5 instance types. Lastly, there's a "bare metal hypervisor" available for i3.metal instances
-	The term “EC2” is sometimes used to refer to the servers themselves, but technically refers more broadly to a whole collection of supporting services, too, like load balancing (CLBs/ALBs/NLBs), IP addresses (EIPs), bootable images (AMIs), security groups, and network drives (EBS) (which we discuss individually in this guide).
-	**💸EC2 pricing** and **cost management** is a complicated topic. It can range from free (on the AWS free tier) to a lot, depending on your usage. Pricing is by instance type, by second or hour, and changes depending on AWS region and whether you are purchasing your instances On-Demand, on the Spot market or pre-purchasing (Reserved Instances).
- **Network Performance:** For some instance types, AWS uses general terms like Low, Medium, and High to refer to network performance. Users have done benchmarking to provide expectations for what these terms can mean.

Back to top :arrow_up:
