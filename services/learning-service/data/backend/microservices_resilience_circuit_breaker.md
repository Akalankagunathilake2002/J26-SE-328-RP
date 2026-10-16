# Microservices Resilience: Circuit Breakers, Bulkheads, and Retry Strategies

## The Problem of Cascading Failures
In distributed microservices, network partitions, high CPU utilization, or database deadlocks in a downstream service can cause request threads in upstream services to block indefinitely. Without proper boundaries, thread pools become exhausted across all tiers, leading to a catastrophic system-wide outage known as a cascading failure.

## The Circuit Breaker Pattern
The Circuit Breaker pattern acts as a protective proxy around fragile remote invocations. It monitors call failure rates across a sliding window and operates in three distinct states:
1. **Closed**: Normal operation. All remote invocations are dispatched. If the failure rate (e.g. HTTP 500s or timeouts) exceeds a configured threshold (such as 50% over a 100-call sliding window), the circuit transitions to **Open**.
2. **Open**: Fast-fail state. Remote requests are immediately rejected without attempting network calls, instantly executing a localized fallback method and preventing thread blocking.
3. **Half-Open**: After a configurable cooldown sleep window (e.g. 15 seconds), the circuit allows a limited trial batch of requests (e.g. 10 calls) to pass through to the downstream service. If all succeed, the circuit resets to **Closed**; if any fail, it resets back to **Open**.

## Auxiliary Resilience Patterns
- **Bulkhead Isolation**: Segregates critical thread pools and connection queues so that saturation in one non-critical domain (e.g. PDF generation) cannot exhaust worker threads allocated for primary user transactions.
- **Exponential Backoff and Jitter**: Retrying transient failures immediately compounds load during an outage (a "retry storm"). Exponential backoff doubles delay between attempts ($t_n = t_0 \times 2^n$), and random jitter decorrelates concurrent retry attempts across clients.
- **Graceful Fallbacks**: Returns cached read-only data, degraded UI defaults, or queues mutations into an asynchronous dead-letter queue (DLQ) when the primary service is unavailable.
