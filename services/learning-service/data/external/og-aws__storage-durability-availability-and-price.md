<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#storage-durability-availability-and-price -->
# AWS Guide: Storage Durability, Availability, and Price

As an illustration of comparative features and price, the table below gives S3 Standard, RRS, IA, in comparison with Glacier, EBS, EFS, and EC2 d2.xlarge instance store using **Virginia region** as of **Sept 2017**.

|                 | Durability (per year)  | Availability “designed” | Availability SLA | Storage (per TB per month)                                                                                               | GET or retrieve (per million) | Write or archive (per million) |
|-----------------|------------------------|-------------------------|------------------|--------------------------------------------------------------------------------------------------------------------------|-------------------------------|--------------------------------|
| **Glacier**     | Eleven 9s              | Sloooow                 | –                | $4                                                                                                                       | $50                           | $50                            |
| **S3 IA**       | Eleven 9s              | 99.9%                   | **99%**          | $12.50                                                                                                                   | $1                            | $10                            |
| ~~**S3 RRS**~~      | ~~**99.99%**~~             | ~~99.99%~~                  | ~~99.9%~~            | ~~$24 (first TB)~~                                                                                                                      | ~~$0.40~~                         | ~~$5~~                             |
| **S3 Standard** | Eleven 9s              | 99.99%                  | 99.9%            | $23                                                                                                                     | $0.40                         | $5                             |
| **EBS**         | **99.8%**              | Unstated                | 99.99%           | $25/$45/**$100**/$125+ (sc1/st1/**gp2**/io1\) |                               |                                |
| **EFS**         | “High”                 | “High”                  | –                | $300                                                                                                                     |                               |                                |
| **EC2 d2.xlarge instance store**  | Unstated | Unstated                | –                | $25.44                                                                                                                   | $0                            | $0                             |

Especially notable items are in **boldface**. Sources: S3 pricing, S3 SLA, S3 FAQ, RRS info (note that this is considered deprecated), Glacier pricing, EBS availability and durability, EBS pricing, EFS pricing, EC2 SLA

EC2
---
