<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/500 -->
# 500 Internal Server Error

The HTTP **`500 Internal Server Error`** server error response status code indicates that the server encountered an unexpected condition that prevented it from fulfilling the request.
This error is a generic "catch-all" response to server issues, indicating that the server cannot find a more appropriate 5XX error to respond with.

If you're a visitor seeing `500` errors on a web page, these issues require investigation by server owners or administrators.
There are many possible causes of `500` errors, including: improper server configuration, out-of-memory (OOM) issues, unhandled exceptions, improper file permissions, or other complex factors.
Server administrators may proactively log occurrences of server error responses, like the `500` status code, with details about the initiating requests to improve the stability of a service in the future.

## Status

```http
500 Internal Server Error
```

## Examples

### 500 server error response

The following request tries to fetch a webpage, but receives a 500 response in return.
The response body contains a page describing the server state with a link to a support page for visitors.
An identifier is contained in the response body for illustration of a method that may help server administrators narrow down the root cause of the problem:

```http
GET /highlights HTTP/1.1
Host: example.com
User-Agent: curl/8.6.0
Accept: */*
```

```http
HTTP/1.1 500 Internal Server Error
Content-Type: text/html;
Content-Length: 123

  500 Internal Server Error

  Internal Server Error
  The server was unable to complete your request. Please try again later.
  If this problem persists, please contact support.
  Server logs contain details of this error with request ID: ABC-123.

```
