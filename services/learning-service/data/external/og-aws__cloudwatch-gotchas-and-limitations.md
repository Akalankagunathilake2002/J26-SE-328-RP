<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#cloudwatch-gotchas-and-limitations -->
# AWS Guide: CloudWatch Gotchas and Limitations

* 🔸Metrics in CloudWatch originate on the hypervisor. The hypervisor doesn't have access to OS information, so certain metrics (most notably memory utilization) are not available unless pushed to CloudWatch from inside the instance.
* 🔸You can not use more than one metric for an alarm.
* 🔸Notifications you receive from alarms will not have any contextual detail; they have only the specifics of the threshold, alarm state, and timing.
* 🔸By default, CloudWatch metric resolution is 1 minute. If you send multiple values of a metric within the same minute, they will be aggregated into minimum, maximum, average and total (sum) per minute.
* 🐥In July 2017, a new high-resolution option was added for CloudWatch metrics and alarms. This feature allows you to record metrics with 1-second resolution, and to evaluate CloudWatch alarms every 10 seconds.
    - The blog post introducing this feature describes how to publish a high-resolution metric to CloudWatch. Note that when calling the `PutMetricData` API, `StorageResolution` is an attribute of each item you send in the `MetricData` array, not a direct parameter of the `PutMetricData` API call.
* 🔸Data about metrics is kept in CloudWatch for 15 months, starting November 2016 (used to be 14 days). Minimum granularity increases after 15 days.

AMIs
----
