<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/410 -->
# 410 Gone

The HTTP **`410 Gone`** client error response status code indicates that the target resource is no longer available at the origin server and that this condition is likely to be permanent.
A 410 response is cacheable by default.

Clients should not repeat requests for resources that return a 410 response, and website owners should remove or replace links that return this code.
If server owners don't know whether this condition is temporary or permanent, a  status code should be used instead.

## Status

```http
410 Gone
```

## Examples

### Requesting an outdated resource

The following `GET` request is for a page with promotional content that is no longer valid:

```http
GET /promotions/summer-2023 HTTP/1.1
Host: example.com
```

```http
HTTP/1.1 410 Gone
Content-Type: text/html
Content-Length: 212

    Promotion expired

    Promotion expired
    Promotion no longer active! See current offers.

```
