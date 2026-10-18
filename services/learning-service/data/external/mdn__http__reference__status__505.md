<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/505 -->
# 505 HTTP Version Not Supported

The HTTP **`505 HTTP Version Not Supported`** server error response status code indicates that the HTTP version used in the request is not supported by the server.

It's common to see this error when a request line is improperly formed such as `GET /path to resource HTTP/1.1` or with `\n` terminating the request line instead of `\r\n`.
For example, intermediaries such as load balancers may not handle request lines of a forwarded request as illustrated in the example below.

## Status

```http
505 HTTP Version Not Supported
```

## Examples

### A 505 due to malformed request-line

In the following example, a client requests `example.com/dog%20trainers`, but due to incorrect load balancer configuration, the percent encoding in the URL is not handled properly.
In this case, the origin server sees `trainers` instead of the HTTP version, and a `505` response is returned instead.
A request identifier is contained in the response body for illustration of a way that may help server administrators narrow down the root cause of the problem:

```http
GET /dog trainers HTTP/1.1
Host: example.com
```

```http
HTTP/1.1 505 HTTP Version Not Supported
Content-Type: text/html;
Content-Length: 123

  505 HTTP Version Not Supported

  505 HTTP Version Not Supported
  If this problem persists, please contact support.
  Server logs contain details of this error with request ID: ABC-123.

```
