<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#iot-gotchas-and-limitations -->
# AWS Guide: IoT Gotchas and Limitations

- 	🔸**IoT protocols:** It is important to verify the exact type of support for your particular IoT device message protocol. For example, one commonly used IoT protocol is MQTT. Within MQTT there are three possible levels of QoS in MQTT.  AWS IoT supports MQTT QoS 0 (fire and forget, or at most once) and QoS 1(at least once, or includes confirmation), but *not* QoS 2 (exactly once, requires 4-step confirmation).  This is important in understanding how much code you’ll need to write for your particular application message resolution needs.  Here is a presentation about the nuances of connecting.
- 	🔸The ecosystems to match **IAM users or roles** to **IoT policies** and their associated authorized AWS IoT devices are immature. Custom coding to enforce your security requirements is common.
- 	❗A common mistake is to misunderstand the importance of IoT **device** **security**.  It is imperative to associate *each* device with a unique certificate (public key). You can generate your own certificates and upload them to AWS, or you can use AWS generated IoT device certificates. It’s best to read and understand AWS’s own guidance on this topic.
- 	🔸There is only one **AWS IoT Gateway** (endpoint) per AWS account. For production scenarios, you’ll probably need to set up multiple AWS accounts in order to separate device traffic for development, test and production. It’s interesting to note that the Azure IoT Gateway supports configuration of multiple endpoints, so that a single Azure account can be used with separate pub/sub endpoints for development, testing and production
- 	🔸**Limits:** Be aware of limits, including device message size, type, frequency, and number of AWS IoT rules.

Back to top :arrow_up:
