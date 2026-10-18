<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/504 -->
# 504 Gateway Timeout

The HTTP **`504 Gateway Timeout`** server error response status code indicates that the server, while acting as a gateway or proxy, did not get a response in time from the upstream server in order to complete the request.
This is similar to a 502 Bad Gateway, except that in a `504` status, the proxy or gateway did not receive any HTTP response from the origin within a certain time.

There are many causes of `504` errors, and fixing such problems likely requires investigation and debugging by server administrators, or the site may work again at a later time.
Exceptions are client networking errors, particularly if the service works for other visitors, and if clients use VPNs or other custom networking setups.
In such cases, clients should check network settings, firewall setup, proxy settings, DNS configuration, etc.

## Status

```http
504 Gateway Timeout
```

## Examples

### 504 gateway timeout response

The following request tries to fetch a webpage, but receives a `504` response in return.
The response body contains a page describing the server state with a link to a support page for visitors.

```http
GET /highlights HTTP/1.1
Host: example.com
User-Agent: curl/8.6.0
Accept: */*
```

```http
HTTP/1.1 504 Gateway Timeout
Content-Type: text/html;
Content-Length: 123

  504 Gateway Timeout

  Gateway timeout
  The server did not respond in time. Please try again later.
  If this problem persists, please contact support.

```
