<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Methods -->
# Access-Control-Allow-Methods header

The HTTP **`Access-Control-Allow-Methods`** response header specifies one or more HTTP request methods allowed when accessing a resource in response to a preflight request.

      Header type
      Response header

## Syntax

```http
Access-Control-Allow-Methods: , , …
Access-Control-Allow-Methods: *
```

## Directives

- ``
  - : A comma-separated list of the allowed request methods. `GET`, `HEAD`, and `POST` are always allowed, regardless of whether they are specified in this header, as they are defined as CORS-safelisted methods.
- `*` (wildcard)
  - : All HTTP methods.
    It has this meaning only for requests without credentials (requests without HTTP cookies or HTTP authentication information). In requests with credentials, it is
    treated as the literal method name `*` without special semantics.

## Examples

```http
Access-Control-Allow-Methods: PUT, DELETE
Access-Control-Allow-Methods: *
```
