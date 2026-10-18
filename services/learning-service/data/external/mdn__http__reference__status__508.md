<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/508 -->
# 508 Loop Detected

The HTTP **`508 Loop Detected`** server error response status code indicates that the entire operation failed because it encountered an infinite loop while processing a request with `Depth: infinity`.

The status may be given in the context of the Web Distributed Authoring and Versioning (WebDAV).
It was introduced as a fallback for cases where WebDAV clients do not support 208 Already Reported responses (when requests do not explicitly include a `DAV` header).

## Status

```http
508 Loop Detected
```

## Examples

### Infinite loop in WebDAV search

```http
PROPFIND /Coll/ HTTP/1.1
Host: example.com
Depth: infinity
Content-Type: application/xml; charset="utf-8"
Content-Length: 125

```

```http
HTTP/1.1 508 Loop Detected
Content-Type: application/json; charset=utf-8
Server: Microsoft-IIS/8.0
Date: Wed, 15 May 2013 02:38:57 GMT
Content-Length: 72

{
  "Message": "Please check the resources for cyclic references and try again."
}
```
