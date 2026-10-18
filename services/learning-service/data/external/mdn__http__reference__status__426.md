<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/426 -->
# 426 Upgrade Required

The HTTP **`426 Upgrade Required`** client error response status code indicates that the server refused to perform the request using the current protocol but might be willing to do so after the client upgrades to a different protocol.

The server sends an Upgrade header with this response to indicate the required protocol(s).

## Status

```http
426 Upgrade Required
```

## Examples

### Upgrade required from HTTP/1.1

Given a GET request to a system:

```http
GET /resources HTTP/1.1
Host: example.com
```

The origin server expects that requests must be made in HTTP/3:

```http
HTTP/1.1 426 Upgrade Required
Upgrade: HTTP/3.0
Connection: Upgrade
Content-Length: 53
Content-Type: text/plain

This service requires use of the HTTP/3.0 protocol.
```
