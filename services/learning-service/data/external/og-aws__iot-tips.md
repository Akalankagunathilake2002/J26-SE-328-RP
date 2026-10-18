<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#iot-tips -->
# AWS Guide: IoT Tips

- 	**Getting started with Buttons:** One way to start is to use an **AWS IoT Button**.  AWS provides a number of code samples for use with their IoT Button, you can use the AWS IoT console, click the “connect AWS IoT button” link and you'll be taken to the  AWS Lambda console.  There you fill out your button’s serial number to associate it with a Lambda. (As of this writing, AWS IoT buttons are only available for sale in the US.)
- 	**Connections and protocols:** It is important to understand the details of about the devices you wish to connect to the AWS IoT service, including how you will secure the device connections, the device protocols, and more. Cloud vendors differ significantly in their support for common IoT protocols, such as MQTT, AMQP, XMPP. AWS IoT supports **secure MQTT**, **WebSockets** and **HTTPS**.
- 	Support for **device security** via certificate processing is a key differentiator in this space.  In August 2016, AWS added just-in-time registrations for IoT devices to their services.
- 	**Combining with other services:** It’s common to use other AWS services, such as AWS Lambda, Kinesis and DynamoDB, although this is by no means required.  Sample IoT application reference architectures are in this screencast.
- 	**Testing tools:**
    *	To get started, AWS includes a lightweight MQTT client in the AWS IoT console. Here you can create and test sending and receiving messages to and from various MQTT topics.
    * 	When testing locally, if using MQTT, it may be helpful to download and use the open source Mosquitto broker tool for local testing with devices and/or device simulators
    * 	Use this MQTT load simulator to test device message load throughout your IoT solution.

Back to top :arrow_up:
