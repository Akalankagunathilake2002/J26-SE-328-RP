<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#elasticache-tips -->
# AWS Guide: ElastiCache Tips

- Choose the
  engine,
  clustering configuration and instance
  type
  carefully based on your application needs. The documentation explains in
  detail the pros, cons and limitations of each engine in order to help you
  choose the best fit for your application. In a nutshell, Redis is
  preferable for storing more complex data structures, while Memcached is just a
  plain key/value store. The simplicity of Memcached allows it to be slightly
  faster and allows it to scale out if needed, but Redis has more features which
  you may use in your application.
- For Memcached AWS provides enhanced SDKs for certain programming languages
  which implement
  auto-discovery,
  a feature not available in the normal memcached client libraries.

Back to top :arrow_up:
