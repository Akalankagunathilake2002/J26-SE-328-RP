# Distributed Tracing and Microservices Observability with OpenTelemetry

## The Three Pillars of Observability
In monolithic applications, debugging a slow transaction involves reading a single log file or profiling a single process. In distributed microservice topologies where a user request touches 15 distinct services, diagnosing bottlenecks requires correlating telemetry across three pillars:
1. **Metrics**: Aggregated quantitative timeseries measurements (e.g. request rate, CPU usage, p99 latency).
2. **Logs**: Discrete, timestamped event records detailing specific operations and stack traces.
3. **Traces**: End-to-end representation of a request's journey across network boundaries and service tiers.

## Core Tracing Anatomy: Spans and Context Propagation
- **Trace**: A directed acyclic graph (DAG) of Spans representing an end-to-end request lifecycle. Identified by a globally unique 128-bit `TraceID`.
- **Span**: A single unit of contiguous work within a system (e.g. an HTTP handler execution or a SQL query). Identified by a `SpanID` and containing start time, end time, attributes (key-value metadata), and events (point-in-time logs).
- **Context Propagation**: To stitch spans together across distributed boundaries, services inject and extract trace headers via W3C Trace Context standards:
  - `traceparent`: `00-{TraceID}-{SpanID}-{TraceFlags}` (e.g. `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`).
  - `tracestate`: Vendor-specific routing and filtering tags.

## OpenTelemetry Architecture
OpenTelemetry (OTel) provides vendor-neutral instrumentation APIs and SDKs:
1. **In-Process SDK**: Intercepts HTTP/gRPC requests, database drivers, and messaging queues to generate traces.
2. **OTel Collector**: A high-performance proxy agent that receives spans via OTLP (OpenTelemetry Protocol), applies sampling rules, scrubs sensitive PII, and exports telemetry to storage backends (Jaeger, Prometheus, Datadog).
3. **Head-Based vs Tail-Based Sampling**:
   - Head-based sampling decides whether to sample a trace at its ingress gateway (e.g. sample 5% of all traffic).
   - Tail-based sampling buffers all spans in the collector and samples 100% of traces that resulted in HTTP 5xx errors or latency exceeding 1,000ms.
