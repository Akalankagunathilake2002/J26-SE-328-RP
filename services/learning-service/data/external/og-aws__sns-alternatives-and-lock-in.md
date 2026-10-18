<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#in -->
# AWS Guide: SNS Alternatives and Lock-In

- Popular alternatives to SNS are Kafka, Notification Hubs on Azure, and Pub/Sub on Google Cloud.
- **SNS vs SQS:**
    - Both SNS and SQS are highly scalable, fully managed messaging services provided by AWS.
    - SQS supports a *pull* model, while SNS supports a *push* model. Consumers have to pull messages from an SQS Queue, while they're pushed the message from an SNS Topic.
    - An SQS message is intended to be processed by only one subscriber, while SNS topics can have many subscribers.
    - After processing, the SQS message is deleted from the queue by the subscriber to avoid being re-processed.
    - An SNS message is *pushed* to all subscribers of the topic at the same time, and is not available for deletion at the topic.
    - SNS supports multiple transport protocols of delivery of the messages to the subscribers, while SQS subscribers have to pull the messages off the queue over HTTPS.

Back to top :arrow_up:
