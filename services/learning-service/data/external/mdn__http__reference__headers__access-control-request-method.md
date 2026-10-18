<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Request-Method -->
# Access-Control-Request-Method header

The HTTP **`Access-Control-Request-Method`** request header is used by browsers when issuing a preflight request to let the server know which HTTP method will be used when the actual request is made.
This header is necessary because the preflight request is always an OPTIONS and doesn't use the same method as the actual request.

      Header type
      Request header

      Forbidden request header
      Yes

## Syntax

```http
Access-Control-Request-Method:
```

## Directives

- ``
  - : An HTTP request method; for example, GET, POST, or DELETE.

## Examples

```http
Access-Control-Request-Method: POST
```
