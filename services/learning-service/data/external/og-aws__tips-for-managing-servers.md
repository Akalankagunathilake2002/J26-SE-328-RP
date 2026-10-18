<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#tips-for-managing-servers -->
# AWS Guide: Tips for Managing Servers

-	❗**Timezone settings on servers**: unless *absolutely necessary*, always **set the timezone on servers to UTC** (see instructions for your distribution, such as Ubuntu, CentOS or Amazon Linux). Numerous distributed systems rely on time for synchronization and coordination and UTC provides the universal reference plane: it is not subject to  daylight savings changes and adjustments in local time. It will also save you a lot of headache debugging elusive timezone issues and provide coherent timeline of events in your logging and audit systems.
-	**NTP and accurate time:** If you are not using Amazon Linux (which comes preconfigured), you should confirm your servers configure NTP correctly, to avoid insidious time drift (which can then cause all sorts of issues, from breaking API calls to misleading logs). This should be part of your automatic configuration for every server. If time has already drifted substantially (generally >1000 seconds), remember NTP won’t shift it back, so you may need to remediate manually (for example, like this on Ubuntu).
-	**Testing immutable infrastructure:** If you want to be proactive about testing your service’s ability to cope with instance termination or failure, it can be helpful to introduce random instance termination during business hours, which will expose any such issues at a time when engineers are available to identify and fix them. Netflix’s Simian Army (specifically, Chaos Monkey) is a popular tool for this. Alternatively, chaos-lambda by the BBC is a lightweight option which runs on AWS Lambda.

Security and IAM
----------------

We cover security basics first, since configuring user accounts is something you usually have to do early on when setting up your system.
