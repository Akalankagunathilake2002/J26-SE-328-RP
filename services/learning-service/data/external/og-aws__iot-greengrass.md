<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#iot-greengrass -->
# AWS Guide: IoT Greengrass

* 📒 Homepage
* 🐥**Greengrass** is a software platform that extends AWS IoT capabilities allowing Lambda functions to be run directly on local devices.  It also enables IoT devices to be able to securely communicate on a local network without having to connect to the cloud.
    * Greengrass includes a local pub/sub message manager that can buffer messages if connectivity is lost so that inbound and outbound messages to the cloud are preserved. Locally deployed Lambda functions can be triggered by local events, messages from the cloud, or other sources.
    * Greengrass includes secure authentication and authorization of devices within the local network and also between the local network and the AWS cloud. It also provides secure, over-the-air software updates of Lambda functions.
*  Greengrass core software includes a message manager object, Lambda runtime, local copy service for IoT Thing (or device) shadows, and a deployment agent to manage Greengrass group configuration.
* **Greengrass groups** are containers for selected IoT devices settings, subscriptions and associated Lambda functions.  In a Greengrass group a device is either a Greengrass core or an IoT device which will be connected that particular Greengrass core.
* The Greengrass core SDK enables Lambda functions to interact with the AWS Greengrass core on which they run in order to publish messages, interact with the local Thing Shadows service, or invoke other deployed Lambda functions.
* The AWS Greengrass Core SDK only supports sending MQTT messages with QoS = 0.
* Shown below is a diagram which shows the architecture of AWS IoT Greengrass services:

Back to top :arrow_up:
