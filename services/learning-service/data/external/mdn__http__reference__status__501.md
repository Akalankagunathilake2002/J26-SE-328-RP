<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/501 -->
# 501 Not Implemented

The HTTP **`501 Not Implemented`** server error response status code means that the server does not support the functionality required to fulfill the request.

A response with this status may also include a Retry-After header, telling the client that they can retry the request after the specified time has elapsed.
A `501` response is cacheable by default unless caching headers instruct otherwise.

`501` is the appropriate response when the server does not recognize the request method and is incapable of supporting it for any resource.
Servers are required to support GET and HEAD, and therefore must not return `501` in response to requests with these methods.
If the server does recognize the method, but intentionally does not allow it, the appropriate response is 405 Method Not Allowed.

If you have visited a web page and you are seeing `501` errors, these issues require investigation and fixing by server owners or administrators.
You can clear your browser cache for the domain, disable proxies if you are using one, or try again later to see if it works as expected.

A `501` response can occur if proxies cannot not handle request methods used in the context of HTTP Extension Framework (2774) applications.
This status can also occur in Web Distributed Authoring and Versioning (WebDAV) when a request method (`SEARCH`, `PROPFIND`) does not have a URL handler configured to process it.

## Status

```http
501 Not Implemented
```

## Examples

### Extension method not supported

In the following HTTP Extension Framework example, a client sends a request with a mandatory extension specified in the `C-MAN` header.
The Connection header specifies that these extensions are to be handled on a hop-by-hop basis.
A proxy refuses to forward the `M-GET` method, and sends a `501` error in response:

```http
M-GET /document HTTP/1.1
Host: example.com
C-Man: "http://www.example.org/"
Connection: C-Man
```

```http
HTTP/1.1 501 Not Implemented
```
