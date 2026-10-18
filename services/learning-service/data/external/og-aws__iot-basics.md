<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#iot-basics -->
# AWS Guide: IoT Basics

* 	📒 Homepage ∙ User guide ∙ FAQ ∙ Pricing
- 	**IoT** is a platform for allowing clients such as IoT devices or software applications (examples) to communicate with the AWS cloud.
- 	Clients are also called **devices** (or **things**) and include a wide variety of device types.  Roughly there are three categories of device types that interact with IoT services by sending message over an IoT protocol to the IoT Pub/Sub-style message broker, which is called the IoT **Device Gateway**:
    * 	Send messages only: For example, the AWS IoT Button on an eddystone beacon.
    * 	Send, receive, and process messages: For example, a simple processing board, such as a **Raspberry Pi** (quick start guide), or an Alexa device, such as the Echo or Echo Dot. These are designed to work with the Alexa skills kit, a programmable voice-enabled service.
- 	AWS has a useful quick-start (using the Console) and a slide presentation on core topics.
* **IoT terms:**
    * 	AWS **IoT Things** (metadata for devices in a registry) and can store device state in a JSON document, which is called a **device shadow**.  Device metadata can also be stored in **IoT Thing Types**. This aids in device metadata management by allowing for reuse of device description and configuration for more than one device.  Note that IoT Thing Types can be deprecated, but not changed — they are immutable.
    * 	AWS **IoT Certificates** (device authentication) are the logical association of a unique certificate to the logical representation of a device. This association can be done in the Console.  In addition, the public key of the certificate must be copied to the physical device. This covers the authentication of devices to a particular AWS Device Gateway (or message broker). You can associate an AWS IoT certificate with an IoT device or you can register your own CA (Certificate Authority) with AWS, generate your own certificate(s) and associate those certificates with your devices via the AWS Console or cli.
    * 	AWS **IoT Policies** (device/topic authorization) are JSON files that are associated to one or more AWS IoT certificates. This authorizes associated devices to publish and/or subscribe to messages from one or more MQTT topics.
    * 	AWS **IoT Rules** are SQL-like queries which allows for reuse of some or all device message data, as described in this presentation, which summarizes design patterns with for IoT Rules.
    * 	Shown below is a diagram which summarizes the flow of messages between the AWS IoT services:

Back to top :arrow_up:
