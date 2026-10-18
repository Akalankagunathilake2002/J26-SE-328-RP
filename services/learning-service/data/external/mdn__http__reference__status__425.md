<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/425 -->
# 425 Too Early

The HTTP **`425 Too Early`** client error response status code indicates that the server was unwilling to risk processing a request that might be replayed to avoid potential replay attacks.

If a client has interacted with a server recently, early data (also known as zero round-trip time (0-RTT) data) allows the client to send data to a server in the first round trip of a connection, without waiting for the TLS handshake to complete.
A client that sends a request in early data does not need to include the `Early-Data` header.
See Early-Data for more information.

## Status

```http
425 Too Early
```
