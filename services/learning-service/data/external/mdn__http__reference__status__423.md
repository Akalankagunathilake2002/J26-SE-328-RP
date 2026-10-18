<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/423 -->
# 423 Locked

The HTTP **`423 Locked`** client error response status code indicates that a resource is _locked_, meaning it can't be accessed.
Its response body should contain information in WebDAV's XML format.

> [!NOTE]
> The ability to _lock_ a resource to prevent conflicts is specific to some WebDAV servers.
> Browsers accessing web pages will never encounter this status code; in the erroneous cases it happens, they will handle it as a generic  status code.

## Status

```http
423 Locked
```

## Examples

### WebDAV 423 Locked response

```http
HTTP/1.1 423 Locked
Content-Type: application/xml; charset="utf-8"
Content-Length: xxxx

    /workspace/web-dav/

```
