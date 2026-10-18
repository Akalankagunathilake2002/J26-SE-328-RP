<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#cloudwatch-tips -->
# AWS Guide: CloudWatch Tips

* Some very common use cases for CloudWatch are **billing alarms**, **instance** **or load balancer up/down alarms**, and **disk usage alerts**.
* You can use EC2Config to monitor watch memory and disk metrics on Windows platform instances. For Linux, there are example scripts that do the same thing.
* You can publish your own metrics using the AWS API. Incurs additional cost.
* You can stream directly from CloudWatch Logs to a Lambda or ElasticSearch cluster by creating subscriptions on Log Groups.
* Don't forget to take advantage of the CloudWatch non-expiring free tier.

Back to top :arrow_up:
