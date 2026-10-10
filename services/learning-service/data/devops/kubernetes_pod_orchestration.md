# Kubernetes Architecture: Pod Orchestration, Services, and Autoscaling

## Core Kubernetes Primitives
Kubernetes is a declarative container orchestration platform automating deployment, scaling, and management of containerized workloads.

1. **Pod**: The smallest deployable computing unit in Kubernetes. Represents a single instance of a running process containing one or more tightly coupled containers sharing network namespaces (`localhost`) and storage volumes.
2. **Deployment**: Declarative controller managing Pod replicas. Handles zero-downtime rolling updates, canary rollouts, and automatic rollbacks upon health failure.
3. **ReplicaSet**: Ensures a specified number of identical Pod replicas are running at any given moment.
4. **Service**: An abstract representation providing a stable IP address and DNS name (`my-service.namespace.svc.cluster.local`) over a dynamic, ephemeral pool of Pods using label selectors.
   - `ClusterIP`: Exposes the service internally within the cluster.
   - `NodePort`: Exposes the service on each node's static port.
   - `LoadBalancer`: Provisions a cloud provider load balancer (AWS ALB, GCP Cloud LB).

## Pod Lifecycle and Health Probes
Kubernetes relies on three distinct container probes to manage pod availability:
- **Startup Probe**: Determines whether the application inside the container has initialized (useful for legacy slow-starting JVM services).
- **Liveness Probe**: Determines whether the container needs to be restarted. If an unrecoverable deadlock occurs, the liveness probe fails, and the kubelet kills and recreates the container.
- **Readiness Probe**: Determines whether a Pod is ready to accept incoming network traffic. If a Pod is warming up caches or database connections, the readiness probe fails, causing the Service to temporarily remove the Pod from endpoint routing without restarting it.

## Autoscaling Mechanics (HPA)
The Horizontal Pod Autoscaler (HPA) automatically adjusts the number of Pod replicas based on observed CPU utilization, memory thresholds, or custom metrics (e.g. Kafka consumer lag):
$$\text{Desired Replicas} = \left\lceil \text{Current Replicas} \times \left( \frac{\text{Current Metric Value}}{\text{Target Metric Value}} \right) \right\rceil$$
When CPU load rises above 75%, HPA scales the Deployment from 3 pods up to its maximum ceiling (e.g. 20 pods) within seconds.
