<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#apis-and-sdks -->
# AWS Guide: APIs and SDKs

-	**SDKs** for using AWS APIs are available in most major languages, with Go, iOS, Java, JavaScript, Python, Ruby, and PHP being most heavily used. AWS maintains a short list, but the awesome-aws list is the most comprehensive and current. Note support for C++ is still new.
-	**Retry logic:** An important aspect to consider whenever using SDKs is error handling; under heavy use, a wide variety of failures, from programming errors to throttling to AWS-related outages or failures, can be expected to occur. SDKs typically implement **exponential backoff** to address this, but this may need to be understood and adjusted over time for some applications. For example, it is often helpful to alert on some error codes and not on others.
-	❗Don’t use APIs directly. Although AWS documentation includes lots of API details, it’s better to use the SDKs for your preferred language to access APIs. SDKs are more mature, robust, and well-maintained than something you’d write yourself.
