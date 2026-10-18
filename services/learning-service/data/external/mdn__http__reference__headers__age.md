<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Age -->
# Age header

The HTTP **`Age`** response header indicates the time in seconds for which an object was in a proxy cache.

The header value is usually close to zero.
If the value is `0`, the object was probably fetched from the origin server; otherwise, the value is usually calculated as a difference between the proxy's current date and the Date general header included in the HTTP response.

      Header type
      Response header

## Syntax

```http
Age:
```

## Directives

- ``
  - : A non-negative integer that represents the time in seconds for which the object was in a proxy cache.

## Examples

```http
Age: 24
```
