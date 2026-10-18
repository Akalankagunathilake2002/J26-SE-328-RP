<!-- role: Backend Developer / DevOps Engineer -->
<!-- topic: System Design -->
<!-- source: The System Design Primer (Donne Martin) -->
<!-- license: CC BY 4.0 -->
<!-- url: https://github.com/donnemartin/system-design-primer#application-layer -->
# System Design: Application layer

Source: Intro to architecting systems for scale

Separating out the web layer from the application layer (also known as platform layer) allows you to scale and configure both layers independently.  Adding a new API results in adding application servers without necessarily adding additional web servers.  The **single responsibility principle** advocates for small and autonomous services that work together.  Small teams with small services can plan more aggressively for rapid growth.

Workers in the application layer also help enable asynchronism.

### Microservices

Related to this discussion are microservices, which can be described as a suite of independently deployable, small, modular services.  Each service runs a unique process and communicates through a well-defined, lightweight mechanism to serve a business goal. 1

Pinterest, for example, could have the following microservices: user profile, follower, feed, search, photo upload, etc.

### Service Discovery

Systems such as Consul, Etcd, and Zookeeper can help services find each other by keeping track of registered names, addresses, and ports.  Health checks help verify service integrity and are often done using an HTTP endpoint.  Both Consul and Etcd have a built in key-value store that can be useful for storing config values and other shared data.

### Disadvantage(s): application layer

* Adding an application layer with loosely coupled services requires a different approach from an architectural, operations, and process viewpoint (vs a monolithic system).
* Microservices can add complexity in terms of deployments and operations.

### Source(s) and further reading

* Intro to architecting systems for scale
* Crack the system design interview
* Service oriented architecture
* Introduction to Zookeeper
* Here's what you need to know about building microservices
