<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: Architecture Styles -->
<!-- source: Azure Architecture Center (Microsoft) -->
<!-- license: CC BY 4.0 -->
<!-- url: https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/web-queue-worker -->
# Web-Queue-Worker architecture style

Learn about the Web-Queue-Worker pattern. Discover benefits, challenges, and implementation by using Azure App Service, Azure Functions, and message queues.

This architecture has two core components. A *web front end* handles client requests, and a *worker* does resource-intensive tasks, long-running workflows, or batch jobs. The web front end communicates with the worker through a *message queue*.

On the left, a client connects to an identity provider and a web front end. The web front end connects to a remote service, a database, and a queue. The database points back to the web front end and goes through a cache. The queue connects to a worker, which points to the database. The database points back to the worker and goes through the cache. On the right, static content connects to a content delivery network, which connects to the client.

This architecture typically uses the following components:

- One or more databases

- A cache to store values from the database for quick reads

- A content delivery network to serve static content

- Remote services, like email or Short Message Service (SMS), that non-Microsoft service providers typically provide

- An identity provider for authentication

The web front end and worker are both stateless. You can store session state in a distributed cache. The worker handles long-running work asynchronously. You can trigger the worker by using queue messages or run it on a schedule for batch processing. The worker is optional if the application has no long-running operations.

The front end might include a web API. A single-page application can consume the web API by making asynchronous HTTP requests, or a native client application can consume it directly.

## When to use this architecture

To implement the Web-Queue-Worker architecture, you typically use managed compute services like Azure App Service, Azure Kubernetes Service (AKS), or Azure Container Apps.

Consider this architecture for the following use cases:

- Applications that have a relatively simple domain

- Applications that have long-running workflows or batch operations

- Scenarios where you prefer managed services over infrastructure as a service (IaaS)

## Benefits

- Straightforward architecture that's easy to understand

- Simple deployment and management

- Clear separation of responsibilities between the front end and worker

- Asynchronous messaging that decouples the front end from the worker

- Ability to scale the front end and worker independently

## Challenges

- Without careful design, the front end and worker can grow into large monolithic components that become difficult to maintain and update.

- Shared data schemas or code modules between the front end and worker can create hidden dependencies.

- The web front end can fail after it writes to the database but before it sends a message to the queue. This failure causes consistency problems because the worker never processes its part of the logic. To address this problem, use techniques like the Transactional Outbox pattern, which routes outgoing messages through a separate queue first. The NServiceBus Transactional Session library supports this approach.

## Best practices

- Expose a well-designed API to the client. For more information, see API design best practices.

- Scale automatically to handle changes in load. For more information, see Autoscaling best practices.

- Cache semistatic data. For more information, see Caching best practices.

- Use a content delivery network to host static content. For more information, see Content delivery network best practices.

- Use polyglot persistence when appropriate. For more information, see Understand data models.

- Partition data to improve scalability, reduce contention, and optimize performance. For more information, see Design a data partitioning strategy.

## Web-Queue-Worker on App Service

This section describes a recommended Web-Queue-Worker architecture that uses App Service.

On the left, a client connects to a web app and to a content delivery network. The web app connects to a queue, which connects to an Azure Functions app. The Functions app connects to Azure SQL Database and Azure Cosmos DB. Azure SQL Database and Azure Cosmos DB connect to Azure Managed Redis and back to the Functions app. Azure Blob Storage connects to the content delivery network.

*Download a Visio file of this architecture.*

### Workflow

- An App Service web app serves as the front end, and an Azure Functions app serves as the worker. Both components run on an App Service plan.

- The message queue uses either Azure Service Bus or Azure Storage queues. The previous diagram shows a Storage queue.

- Azure Managed Redis stores session state and other data that requires low-latency access.

- Azure Content Delivery Network caches static content like images, CSS, and HTML.

- For storage, choose the technologies that best fit your application's needs. This approach, known as *polyglot persistence*, combines multiple storage technologies in one system to meet different requirements. The previous diagram demonstrates this approach by using Azure SQL Database and Azure Cosmos DB.

For more information, see Baseline highly available zone-redundant web application and Build message-driven business applications by using NServiceBus and Service Bus.

### Other considerations

- Not every transaction must go through the queue and worker to storage. The web front end can handle simple read and write operations directly. Reserve workers for resource-intensive tasks or long-running workflows. If your application has no such tasks, you might not need a worker.

- Use the built-in autoscale feature of your compute platform to scale out instances. If the load follows predictable patterns, use schedule-based autoscaling. If the load is unpredictable, use metrics-based autoscaling.

- Consider placing the web app and Functions app in separate App Service plans so that they can scale independently.

- Use separate App Service plans for production and testing environments.

- Use deployment slots to manage deployments for App Service plans. Deploy an updated version to a staging slot, then swap over to the new version. If problems occur, swap back to the previous version.

## Related resource

- Queue-Based Load Leveling pattern
