<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#sqs-basics -->
# AWS Guide: SQS Basics

- 📒  _Homepage_ ∙ _Documentation_ ∙ _FAQ_ ∙ _Pricing_
- SQS is a highly scalable, fully managed message queuing service from AWS.
- SQS supports the pull model, where the producers *queue* the messages, and the consumers pull messages off the queue.
- SQS provides a message visibility timeout, during which the message being processed will not be delivered to other consumers. If the consumer does not delete the message after processing, the message becomes available to other consumers upon reaching the message visibility timeout. This parameter is called VisibilityTimeout.
- Each message can have up to 10 custom fields, or attributes.
- SQS allows producers to set up to 15 minutes of delay before the messages are delivered to the consumers. This parameter is called DelaySeconds.
- There are two types of queues supported by SQS -
    - Standard Queues
        - Guarantee **at least once** delivery of the messages.
        - Do not retain the order of delivery of the messages.
    - FIFO Queues
        - Guarantee **only once** delivery of the messages
        - Guarantee the order of the delivery of the messages
- SQS supports fine grained access to various API calls and Queues via IAM policies.
- The messages that fail to process can be put in a dead letter queue.

Back to top :arrow_up:
