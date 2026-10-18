<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/416 -->
# 416 Range Not Satisfiable

The HTTP **`416 Range Not Satisfiable`** client error response status code indicates that a server could not serve the requested ranges.
The most likely reason for this response is that the document doesn't contain such ranges, or that the Range header value, though syntactically correct, doesn't make sense.

The `416` response message should contain a Content-Range indicating an unsatisfied range (that is a `'*'`) followed by a `'/'` and the current length of the resource, e.g., `Content-Range: bytes */12777`

When encountering this error, browsers typically either abort the operation (for example, a download will be considered non-resumable) or request the whole document again without ranges.

## Status

```http
416 Range Not Satisfiable
```

## Examples

### Malformed range request

The following request asks for a range of 1000-1999 bytes from a text file.
The first position unit (1000) is larger than the actual resource on the server (800 bytes):

```http
GET /files/prose.txt HTTP/1.1
Host: example.com
Range: bytes=1000-1999
```

The server supports range requests and sends back the current length of the selected representation in the Content-Range header:

```http
HTTP/1.1 416 Range Not Satisfiable
Date: Fri, 28 Jun 2024 11:40:58 GMT
Content-Range: bytes */800
```
