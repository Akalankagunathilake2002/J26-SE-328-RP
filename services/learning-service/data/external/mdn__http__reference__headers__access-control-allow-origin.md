<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Origin -->
# Access-Control-Allow-Origin header

The HTTP **`Access-Control-Allow-Origin`** response header indicates whether the response can be shared with requesting code from the given origin.

      Header type
      Response header

## Syntax

```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Origin:
Access-Control-Allow-Origin: null
```

## Directives

- `*` (wildcard)
  - : The requesting code from any origin is allowed to access the resource.
    For requests _without credentials_, the literal value `*` can be specified as a wildcard.
    Attempting to use the wildcard with credentials results in an error.
- ``
  - : Specifies a single origin. If the server supports clients from multiple origins, it must return the origin for the specific client making the request.
- `null`
  - : Specifies the origin "null".
    > [!NOTE]
    > The value `null` should not be used. It may seem safe to return `Access-Control-Allow-Origin: "null"`; however, the origin of resources that use a non-hierarchical scheme (such as `data:` or `file:`) and sandboxed documents is serialized as `null`.
    > Many browsers will grant such documents access to a response with an `Access-Control-Allow-Origin: null` header, and any origin can create a hostile document with a `null` origin.
    > Therefore, the `null` value for the `Access-Control-Allow-Origin` header should be avoided.

## Examples

A response that tells the browser to allow code from any origin to access a resource will include the following:

```http
Access-Control-Allow-Origin: *
```

A response that tells the browser to allow requesting code from the origin `https://developer.mozilla.org` to access a resource will include the following:

```http
Access-Control-Allow-Origin: https://developer.mozilla.org
```

Limiting the possible `Access-Control-Allow-Origin` values to a set of allowed origins requires code on the server side to check the value of the Origin request header, compare that to a list of allowed origins, and then if the Origin value is in the list, set the `Access-Control-Allow-Origin` value to the same value as the Origin value.

### CORS and caching

Suppose the server sends a response with an `Access-Control-Allow-Origin` value with an explicit origin (rather than the `*` wildcard). In that case, the response should also include a Vary response header with the value `Origin` — to indicate to browsers that server responses can differ based on the value of the `Origin` request header.

```http
Access-Control-Allow-Origin: https://developer.mozilla.org
Vary: Origin
```
