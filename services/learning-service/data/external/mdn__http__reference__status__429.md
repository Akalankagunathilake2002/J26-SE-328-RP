<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429 -->
# 429 Too Many Requests

The HTTP **`429 Too Many Requests`** client error response status code indicates the client has sent too many requests in a given amount of time.
This mechanism of asking the client to slow down the rate of requests is commonly called "rate limiting".

A Retry-After header may be included to this response to indicate how long a client should wait before making the request again.

Implementations of rate limiting vary; restrictions may be server-wide or per resource.
Typically, rate-limiting restrictions are based on a client's IP but can be specific to users or authorized applications if requests are authenticated or contain a cookie.

## Status

```http
429 Too Many Requests
```

## Examples

### Response containing Retry-After header

The following request is being sent repeatedly in a loop by a client that is misconfigured:

```http
GET /reports/mdn HTTP/1.1
Host: example.com
```

In this example, server-wide rate limiting is active when a client exceeds a set threshold of requests per minute.
A 429 response is returned with a Retry-After header that indicates requests will be allowed for this client again after 3600 seconds (60 minutes):

```http
HTTP/1.1 429 Too Many Requests
Content-Type: text/html
Retry-After: 3600

    Too Many Requests

    Too Many Requests
    You're doing that too often! Try again later.

```
