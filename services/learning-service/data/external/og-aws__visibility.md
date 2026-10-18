<!-- role: DevOps Engineer -->
<!-- topic: AWS Cloud Services -->
<!-- source: The Open Guide to AWS -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/open-guides/og-aws#visibility -->
# AWS Guide: Visibility

-	Store and track instance metadata (such as instance id, availability zone, etc.) and deployment info (application build id, Git revision, etc.) in your logs or reports. The **instance metadata service** can help collect some of the AWS data you’ll need.
-	**Use log management services:** Be sure to set up a way to view and manage logs externally from servers.
	-	Cloud-based services such as Sumo Logic, Splunk Cloud, Scalyr, LogDNA, and Loggly are the easiest to set up and use (and also the most expensive, which may be a factor depending on how much log data you have).
	-	Major open source alternatives include Elasticsearch, Logstash, and Kibana (the “Elastic Stack”) and Graylog.
	-	If you can afford it (you have little data or lots of money) and don’t have special needs, it makes sense to use hosted services whenever possible, since setting up your own scalable log processing systems is notoriously time consuming.
-	**Track and graph metrics:** The AWS Console can show you simple graphs from CloudWatch, you typically will want to track and graph many kinds of metrics, from CloudWatch and your applications. Collect and export helpful metrics everywhere you can (and as long as volume is manageable enough you can afford it).
	-	Services like Librato, KeenIO, and Datadog have fancier features or better user interfaces that can save a lot of time. (A more detailed comparison is here.)
	-	Use Prometheus or Graphite as timeseries databases for your metrics (both are open source).
	-	Grafana can visualize with dashboards the stored metrics of both timeseries databases (also open source).

Back to top :arrow_up:
