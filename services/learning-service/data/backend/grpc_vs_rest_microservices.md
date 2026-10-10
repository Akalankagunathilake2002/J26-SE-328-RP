# Inter-Service Communication: gRPC vs RESTful HTTP APIs

## Protocol Fundamentals: JSON/HTTP/1.1 vs Protobuf/HTTP/2
While REST over JSON remains standard for public client-facing APIs, internal east-west microservice traffic incurs substantial CPU and network serialization overhead:
- **REST / JSON**: Text-based formatting with human-readable keys repeated in every payload, parsed via string parsing and reflection.
- **gRPC**: Uses Protocol Buffers (Protobuf) binary serialization. Fields are indexed by numerical tags rather than verbose string keys, resulting in payloads up to 70% smaller and serialization speeds 5 to 10 times faster than JSON.

## HTTP/2 Transport Advantages
gRPC runs natively over HTTP/2, unlocking:
1. **Binary Framing**: Divides communication into structured frames instead of ASCII strings.
2. **Multiplexing**: Multiple concurrent RPC calls execute across a single persistent TCP connection simultaneously, eliminating head-of-line blocking and connection handshake costs.
3. **Header Compression (HPACK)**: Compresses repeated headers across calls.
4. **Streaming Modes**:
   - Unary RPC (standard request/response).
   - Server Streaming (server sends stream of events/chunks).
   - Client Streaming (client streams data chunks before single server response).
   - Bidirectional Streaming (full-duplex simultaneous communication).

## Production Architectural Trade-Offs
- **Contract-First Rigor**: Protobuf schemas (`.proto` files) serve as the strict, strongly-typed single source of truth. Breaking changes are caught at compile-time across Polyglot codebases (Go, Java, Python, C#).
- **Tooling & Debuggability**: REST benefits from universal browser inspection, cURL, and Swagger/OpenAPI. Debugging gRPC requires specialized tooling like `grpcurl` or Envoy gateway transcoding.
- **Edge Architecture**: Production architectures typically adopt a Hybrid Pattern: REST/GraphQL at the API Gateway edge for external browser/mobile clients, and gRPC for internal high-throughput inter-service RPCs.
