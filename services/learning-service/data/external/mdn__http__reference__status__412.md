<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/412 -->
# 412 Precondition Failed

The HTTP **`412 Precondition Failed`** client error response status code indicates that access to the target resource was denied.
This happens with conditional requests on methods other than GET or HEAD when the condition defined by the If-Unmodified-Since or If-Match headers is not fulfilled.
In that case, the request (usually an upload or a modification of a resource) cannot be made and this error response is sent back.

## Status

```http
412 Precondition Failed
```

## Examples

### Precondition failed

```http
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
ETag: W/"0815"
```

### Avoiding mid-air collisions

With the help of the `ETag` and the If-Match headers, you can prevent conflicts or mid-air collisions.
For example, when editing some wiki pages, content is hashed and put into an `ETag` in successful responses:

```http
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

When saving changes to a wiki page (posting data), the POST request will contain the If-Match header containing the `ETag` values that the client stored from the last edit to check freshness of the resource on the server:

```http
If-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"
```

If the hashes don't match, the document has been edited in-between and a `412 Precondition Failed` error is thrown.
