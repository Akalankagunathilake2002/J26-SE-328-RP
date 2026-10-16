# Real-Time Web Architectures: WebSockets vs Server-Sent Events vs Long-Polling

## Real-Time Protocols Comparison
1. **Short Polling**:
   - Client sends regular HTTP requests at fixed intervals (e.g., every 3 seconds).
   - Inefficient: 95% of requests return empty responses (`204 No Content`), generating high CPU and network overhead from repeated TCP/TLS handshakes and HTTP header exchanges.

2. **Long Polling**:
   - Client sends an HTTP request; server holds the connection open until new data arrives or a timeout occurs (e.g., 30 seconds).
   - *Advantage*: Works over restrictive enterprise firewalls without WebSocket support.
   - *Drawback*: Connection teardown and re-establishment overhead on every message.

3. **Server-Sent Events (SSE)**:
   - Unidirectional server-to-client streaming over standard HTTP (`Content-Type: text/event-stream`).
   - Native browser support via `EventSource` API with automatic reconnection, event IDs, and message deduplication.
   - *Best Suited For*: Real-time dashboards, live financial tickers, LLM token streaming, notifications.

4. **WebSockets (RFC 6455)**:
   - Full-duplex, bidirectional persistent connection over a single TCP socket.
   - Initiated via an HTTP Upgrade handshake (`Connection: Upgrade`, `Upgrade: websocket`).
   - Frames carry minimal framing overhead (2 to 10 bytes) with zero HTTP header duplication.
   - *Best Suited For*: Multiplayer collaboration tools, high-frequency chat, online gaming, bidirectional interactive AI avatars.

## Scalability and Connection State in Clustered Environments
Because WebSockets maintain stateful TCP connections, scaling WebSocket servers across Kubernetes pods requires:
- **Redis Pub/Sub Socket Adapter**: When User A (connected to Pod 1) messages User B (connected to Pod 2), Pod 1 publishes the event to Redis, which broadcasts it to Pod 2 for delivery over User B's open socket.
- **Heartbeat / Ping-Pong Keepalive**: Periodic small ping frames prevent stateful cloud load balancers (AWS ALB, Nginx) from dropping idle connections due to inactivity timeouts.
