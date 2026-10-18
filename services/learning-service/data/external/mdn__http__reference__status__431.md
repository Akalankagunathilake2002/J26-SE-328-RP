<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/431 -->
# 431 Request Header Fields Too Large

The HTTP **`431 Request Header Fields Too Large`** client error response status code indicates that the server refuses to process the request because the request's HTTP headers are too long.
The request may be resubmitted after reducing the size of the request headers.

431 can be used when the total size of request headers is too large or when a single header field is too large.
To help clients running into this error, indicate which of the two is the problem in the response body and, ideally, say which headers are too large.
This lets people attempt to fix the problem, such as by clearing cookies.

Servers will often produce this status if:

- The Referer URL is too long
- There are too many Cookies sent in the request

## Status

```http
431 Request Header Fields Too Large
```

## Examples

### Header field too large

In the following example, the Cookie header is too large in the request:

```http
GET /doc HTTP/1.1
Host: example.com
Cookie: cookie1=value1; cookie2=value2; cookie3=[…]
```

The server responds with a message indicating which header was problematic:

```http
HTTP/1.1 431 Request Header Fields Too Large
Content-Type: text/html

    Request Header Fields Too Large

    Request Header Fields Too Large
    The "Cookie" header was too large.

```
