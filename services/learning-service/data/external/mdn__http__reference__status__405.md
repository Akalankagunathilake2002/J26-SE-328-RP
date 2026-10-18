<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/405 -->
# 405 Method Not Allowed

The HTTP **`405 Method Not Allowed`** client error response status code indicates that the server knows the request method, but the target resource doesn't support this method.
The server **must** generate an Allow header in a 405 response with a list of methods that the target resource currently supports.

Improper server-side permissions set on files or directories may cause a 405 response when the request would otherwise be expected to succeed.

## Status

```http
405 Method Not Allowed
```

## Examples

### TRACE method not allowed

Server owners often disallow the use of the `TRACE` method due to security concerns.
The following example shows a typical response where a server doesn't allow the use of `TRACE`:

```http
TRACE / HTTP/1.1
Host: example.com
```

```http
HTTP/1.1 405 Method Not Allowed
Content-Length: 0
Date: Fri, 28 Jun 2024 14:30:31 GMT
Server: ECLF (nyd/D179)
Allow: GET, POST, HEAD
```
