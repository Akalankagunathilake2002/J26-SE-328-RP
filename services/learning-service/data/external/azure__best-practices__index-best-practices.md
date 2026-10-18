<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: Cloud Best Practices -->
<!-- source: Azure Architecture Center (Microsoft) -->
<!-- license: CC BY 4.0 -->
<!-- url: https://learn.microsoft.com/en-us/azure/architecture/best-practices/index-best-practices -->
# Best practices in cloud applications

Learn about some best practices for building cloud applications and how they align with the Azure Well-Architected Framework.

Building reliable, scalable, and secure cloud applications requires deliberate architectural decisions. The best practices in this article provide guidance for common concerns that arise in distributed systems, such as caching, data partitioning, API design, and transient fault handling. Each practice addresses one or more pillars of the Azure Well-Architected Framework, which defines the following five quality attributes for workload design:

- Reliability
- Security
- Cost Optimization
- Operational Excellence
- Performance Efficiency

These practices complement other foundational guidance in the Azure Architecture Center. The design principles for Azure applications provide high-level strategies, like designing for self-healing and scaling out. The cloud design patterns offer reusable solutions to recurring architectural problems. The performance antipatterns describe common defects that cause scalability problems under load. These resources help you make informed architectural choices.

## Catalog of practices

Each practice in this table maps to one or more Well-Architected Framework pillars. Use these mappings to identify which practices are most relevant to the quality attributes that you prioritize in your workload.

| Practice | Summary | Related pillars |
| :------- | :------ | :-------------- |
| API design | Design web APIs to support platform independence by using standard protocols and agreed-upon data formats. Promote service evolution so that clients can discover functionality without requiring modification. Improve response times by supporting partial responses and providing ways to filter and paginate data. | Operational Excellence, Performance Efficiency |
| API implementation | Implement web APIs to be efficient, responsive, scalable, and available. Make actions idempotent, support content negotiation, and follow the HTTP specification. Handle exceptions and support the discovery of resources. Provide ways to handle large requests and minimize network traffic. | Operational Excellence, Performance Efficiency |
| Autoscaling | Design apps to dynamically allocate and deallocate resources to satisfy performance requirements and minimize costs. Take advantage of the autoscale feature in Azure Monitor and the built-in autoscaling that many Azure components provide. | Cost Optimization, Performance Efficiency |
| Background jobs | Implement batch jobs, processing tasks, and workflows as background jobs. Use Azure platform services to host these tasks. Use events or schedules to trigger tasks, and return results to calling tasks. | Reliability, Operational Excellence |
| Caching | Improve performance by copying data to fast storage that's close to apps. Cache data that you read often but rarely modify. Manage data expiration and concurrency. See how to populate caches and use the Azure Managed Redis service. | Performance Efficiency |
| Content Delivery Network | Use content delivery networks (CDNs) to efficiently deliver web content to users and reduce load on web apps. Overcome deployment, versioning, security, and resilience challenges. | Reliability, Performance Efficiency |
| Data partitioning | Partition data to improve scalability, availability, and performance and to reduce contention and data storage costs. Use horizontal, vertical, and functional partitioning in efficient ways. | Cost Optimization, Performance Efficiency |
| Data partitioning strategies (by service) | Apply partitioning strategies across Azure services, including Azure SQL Database, Azure Cosmos DB, Azure Blob Storage, Azure Managed Redis, and Azure Service Bus. Distribute loads, reduce latency, and support horizontal scaling. | Cost Optimization, Performance Efficiency |
| Host name preservation | Learn why it's important to preserve the original HTTP host name between a reverse proxy and its back-end web application and how to implement this recommendation for the most common Azure services. | Reliability, Security |
| Message encoding considerations | Choose the payload structure, encoding format, and serialization library for asynchronous messages exchanged between system components. Consider trade-offs, such as interoperability, size, human readability, and schema evolution. | Security |
| Monitoring and diagnostics | Track system health, usage, and performance by using a monitoring and diagnostics pipeline. Turn monitoring data into alerts, reports, and triggers that help you take action in various situations. Examples include detecting and correcting issues, catching potential problems, meeting performance guarantees, and fulfilling auditing requirements. | Operational Excellence |
| Transient fault handling | Handle transient faults caused by unavailable networks or resources. Overcome challenges with developing appropriate retry strategies. Avoid duplicating layers of retry code and other antipatterns. | Reliability |

## Design principles

Before you address specific technical concerns, establish a strong architectural foundation. The design principles for Azure applications provide high-level strategies that apply across workloads, such as designing for self-healing, scaling out, and minimizing coordination. These principles shape decisions that the best practices listed in the previous table help you implement.

## Cloud design patterns

After you establish design principles, cloud design patterns give you reusable solutions for recurring problems in distributed systems. Many of the best practices in this article rely on one or more of these patterns. For example, the transient fault handling guidance builds on the Retry pattern and Circuit Breaker pattern. The caching guidance relates to the Cache-Aside pattern. The background jobs guidance uses patterns like Competing Consumers and Queue-Based Load Leveling. Review the full catalog to identify patterns that address the architectural challenges in your workload.

## Performance antipatterns

Defects can emerge under production load even when you apply sound principles, good patterns, and best practices. Performance antipatterns for cloud applications describe common designs that don't scale or shortcuts that cause problems to accumulate as you add features. To catch problems before they reach production, use these antipatterns as a checklist during design reviews and code reviews.

## Next step

- Design principles for Azure applications: Start with the foundational principles that inform these best practices.

## Related content

- Azure Well-Architected Review: Assess your workload against the Well-Architected Framework pillars.

- Cloud design patterns: Explore reusable solutions to common architectural challenges.
