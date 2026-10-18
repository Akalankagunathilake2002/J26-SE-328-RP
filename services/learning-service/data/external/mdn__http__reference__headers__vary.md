<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Vary -->
# Vary header

The HTTP **`Vary`** response header describes the parts of the request message (aside from the method and URL) that influenced the content of the response it occurs in.
Including a `Vary` header ensures that responses are separately cached based on the headers listed in the `Vary` field.
Most often, this is used to create a cache key when content negotiation is in use.

The same `Vary` header value should be used on all responses for a given URL, including 304 `Not Modified` responses and the "default" response.

      Header type
      Response header

## Syntax

```http
Vary: *
Vary: , …,
```

## Directives

- `*` (wildcard)
  - : Factors other than request headers influenced the generation of this response. Implies that the response is uncacheable.
- ``
  - : A request header name that could have influenced the generation of this response.
