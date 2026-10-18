<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#ebs-tips -->
# AWS Guide: EBS Tips

-	⏱**RAID:** Use RAID drives for increased performance.
-	⏱A worthy read is AWS’ post on EBS IO characteristics as well as their performance tips.
-	⏱One can provision IOPS (that is, pay for a specific level of I/O operations per second) to ensure a particular level of performance for a disk.
-	⏱A single gp2 EBS volume allows 16k IOPS max To get the maximum performance out of a gp2 EBS volume, it has to be of a maximum size and attached to an EBS-optimized EC2 instance.
- 	💸Standard and gp2 EBS volumes improve IOPS with size. It may make sense for you to simply enlarge a volume instead of paying for better performance explicitly. This can in many cases reduce costs by 2/3.
-	A standard block size for an EBS volume is 16kb.

Back to top :arrow_up:
