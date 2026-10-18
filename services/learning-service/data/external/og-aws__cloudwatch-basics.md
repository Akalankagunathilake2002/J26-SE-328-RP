<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#cloudwatch-basics -->
# AWS Guide: CloudWatch Basics

* 📒  Homepage ∙ Documentation ∙ FAQ ∙ Pricing
* **CloudWatch** monitors resources and applications, captures logs, and sends events.
* CloudWatch monitoring is the standard mechanism for keeping tabs on AWS resources. A wide range of  **metrics and dimensions** are available via CloudWatch, allowing you to create time based graphs, **alarms**, and **dashboards**.
    * Alarms are the most practical use of CloudWatch, allowing you to trigger notifications from any given metric.
    * Alarms can trigger SNS notifications, Auto Scaling actions, or EC2 actions.
    * Alarms also support alerting when any M out of N datapoints cross the alarm threshold.
    * Publish and share graphs of metrics by creating customizable dashboard views.
		* Monitor and report on EC2 instance system check failure alarms.
* **Using CloudWatch Events:**
    * Events create a mechanism to automate actions in various services on AWS. You can create event rules from instance states, AWS APIs, Auto Scaling, Run commands, deployments or time-based schedules (think Cron).
    * Triggered events can invoke Lambda functions, send SNS/SQS/Kinesis messages, or perform instance actions (terminate, restart, stop, or snapshot volumes).
    * Custom payloads can be sent to targets in JSON format, this is especially useful when triggering Lambdas.
* **Using CloudWatch Logs:**
    * CloudWatch Logs is a streaming log storage system. By storing logs within AWS you have access to unlimited paid storage, but you also have the option of streaming logs directly to ElasticSearch or custom Lambdas.
    * A log agent installed on your servers will process logs over time and send them to CloudWatch Logs.
    * You can export logged data to S3 or stream results to other AWS services.
    * CloudWatch Logs can be encrypted using keys managed through KMS.
* **Detailed monitoring:** Detailed monitoring for EC2 instances must be enabled to get granular metrics, and is billed under CloudWatch.

Back to top :arrow_up:
