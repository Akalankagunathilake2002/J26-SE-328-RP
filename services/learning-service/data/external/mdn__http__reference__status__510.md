<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/510 -->
# 510 Not Extended

The HTTP **`510 Not Extended`** server error response status code is sent when the client request declares an HTTP Extension (2774) that should be used to process the request, but the extension is not supported.

## Status

```http
510 Not Extended
```

## Examples

### Extension not supported

In the following example, a client sends a request with a mandatory extension specified in the `C-MAN` header.
The Connection header specifies that these extensions are to be handled on a hop-by-hop basis.
A proxy forwards the extended request, but the Connection header is stripped out in transit.
Because the origin server doesn't receive any information about the `M-GET` method, it sends a `510` in response:

```http
M-GET /document HTTP/1.1
Host: example.com
C-Man: "http://www.example.org/"
Connection: C-Man
```

```http
HTTP/1.1 510 Not Extended
```
