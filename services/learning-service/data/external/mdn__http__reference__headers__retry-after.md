<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Retry-After -->
# Retry-After header

The HTTP **`Retry-After`** response header indicates how long the user agent should wait before making a follow-up request.
There are three main cases this header is used:

- In a 503 Service Unavailable response, this indicates how long the service is expected to be unavailable.
- In a 429 Too Many Requests response, this indicates how long to wait before making a new request.
- In a redirect response, such as 301 Moved Permanently, this indicates the minimum time that the user agent is asked to wait before issuing the redirected request.

      Header type
      Response header

## Syntax

```http
Retry-After:
Retry-After:
```

## Directives

- ``
  - : A date after which to retry. See the Date header for more details
    on the HTTP date format.
- ``
  - : A non-negative decimal integer indicating the seconds to delay after the response is
    received.

## Examples

### Dealing with scheduled downtime

Support for the `Retry-After` header on both clients and servers is still
inconsistent. However, some crawlers and spiders, like the Googlebot, honor the
`Retry-After` header. It is useful to send it along with a `503` response, so that search engines will keep
indexing your site when the downtime is over.

```http
Retry-After: Wed, 21 Oct 2015 07:28:00 GMT
Retry-After: 120
```
