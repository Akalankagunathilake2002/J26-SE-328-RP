<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Max-Age -->
# Access-Control-Max-Age header

The HTTP **`Access-Control-Max-Age`** response header indicates how long the results of a preflight request (that is, the information contained in the Access-Control-Allow-Methods and Access-Control-Allow-Headers headers) can be cached.

      Header type
      Response header

## Syntax

```http
Access-Control-Max-Age:
```

## Directives

- ``
  - : Maximum number of seconds for which the results can be cached as an unsigned non-negative integer.
    Firefox caps this at 24 hours (86400 seconds).
    Chromium (prior to v76) caps at 10 minutes (600 seconds).
    Chromium (starting in v76) caps at 2 hours (7200 seconds).
    The default value is 5 seconds.

## Examples

Cache results of a preflight request for 10 minutes:

```http
Access-Control-Max-Age: 600
```
