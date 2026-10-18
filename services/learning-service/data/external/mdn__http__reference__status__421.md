<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/421 -->
# 421 Misdirected Request

The HTTP **`421 Misdirected Request`** client error response status code indicates that the request was directed to a server that is not able to produce a response.
This can be sent by a server that is not configured to produce responses for the combination of scheme and authority that are included in the request URI.

Clients may retry the request over a different connection.

## Status

```http
421 Misdirected Request
```

## Examples

### Apache SNI error

Given the following request:

```http
GET / HTTP/1.1
Host: abc.example.com
```

In cases such as a wildcard certificate (`*.example.com`) where a connection is reused for multiple domains (`abc.example.com`, `def.example.com`), the server may respond with a 421:

```http
HTTP/1.1 421 Misdirected Request
Date: Wed, 26 Jun 2024 12:00:00 GMT
Server: Apache/2.4.1 (Unix)
```
