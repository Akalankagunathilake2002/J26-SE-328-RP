<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#ebs-gotchas-and-limitations -->
# AWS Guide: EBS Gotchas and Limitations

-	❗EBS durability is reasonably good for a regular hardware drive (annual failure rate of between 0.1% - 0.2%). On the other hand, that is very poor if you don’t have backups! By contrast, S3 durability is extremely high. *If you care about your data, back it up to S3 with snapshots.*
-	🔸EBS has an **SLA** with **99.99%** uptime. See notes on high availability below.
-	❗EBS volumes have a **volume type** indicating the physical storage type. The types called “standard” (**st1** or **sc1**) are actually old spinning-platter disks, which deliver only hundreds of IOPS — not what you want unless you’re really trying to cut costs. Modern SSD-based **gp2** or **io1** are typically the options you want.
-	❗When restoring a snapshot to create an EBS volume, blocks are lazily read from S3 the first time they're referenced. To avoid an initial period of high latency, you may wish to use `dd` or `fio` as per the official documentation.

EFS
---
