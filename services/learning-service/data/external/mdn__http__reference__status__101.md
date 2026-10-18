<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/101 -->
# 101 Switching Protocols

The HTTP **`101 Switching Protocols`** informational response status code indicates the protocol that a server has switched to.
The protocol is specified in the Upgrade request header received from a client.

The server includes an Upgrade header in this response to indicate the protocol it has agreed to switch to.
The process is described in detail in the Protocol upgrade mechanism guide.

## Status

```http
101 Switching Protocols
```

## Examples

### Switching protocols to WebSockets

The following example shows how switching protocols might be used with WebSockets.
A client sends a GET HTTP request with an Upgrade header which must also be listed in the Connection header.
The server agrees to switch protocols, returning a 101 response meaning the connection has switched from HTTP to WebSocket.
At this point, the client and server can now start exchanging WebSocket data.
Information about how to set `Sec-WebSocket-*` headers for handshake negotiation can be found in WebSocket-specific headers.

```http
GET /notifications HTTP/1.1
Host: example.com
Upgrade: websocket
Connection: Upgrade
```

```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
```
