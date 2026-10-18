<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/308 -->
# 308 Permanent Redirect

The HTTP **`308 Permanent Redirect`** redirection response status code indicates that the requested resource has been permanently moved to the URL given by the Location header.

A browser receiving this status will automatically request the resource at the URL in the `Location` header, redirecting the user to the new page.

The request method and the body **will not be modified** by the client in the redirected request.
A 301 Moved Permanently requires the request method and the body to remain unchanged when redirection is performed, but this is incorrectly handled by older clients to use the GET method instead.

> [!NOTE]
> Some Web applications may use the `308 Permanent Redirect` in a non-standard way and for different purposes.
> For example, Google Drive uses a `308 Resume Incomplete` response to indicate to the client when an unfinished upload has stalled.
> See Perform a resumable download on the Google Drive documentation for more information.

## Status

```http
308 Permanent Redirect
```

## Examples

### 308 response to a moved resource

```http
GET /featured HTTP/1.1
Host: www.example.org
```

```http
HTTP/1.1 308 Permanent Redirect
Location: http://www.example.com/featured
Content-Length: 0
```
