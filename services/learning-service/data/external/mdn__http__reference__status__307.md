<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/307 -->
# 307 Temporary Redirect

The HTTP **`307 Temporary Redirect`** redirection response status code indicates that the resource requested has been temporarily moved to the URL in the Location header.

A browser receiving this status will automatically request the resource at the URL in the `Location` header, redirecting the user to the new page.
Search engines receiving this response will not attribute links to the original URL to the new resource, meaning no SEO value is transferred to the new URL.

The method and the body of the original request are reused to perform the redirected request.
In the cases where you want the request method to be changed to GET, use 303 See Other instead.
This is useful when you want to give an answer to a successful PUT request that is not the uploaded resource, but a status monitor or confirmation message like "You have successfully uploaded XYZ".

The difference between `307` and 302 is that `307` guarantees that the client **will not change** the request method and body when the redirected request is made.
With `302`, older clients incorrectly changed the method to GET.
`307` and `302` responses are identical when the request method is GET.

## Status

```http
307 Temporary Redirect
```

## Examples

### 307 response to a moved resource

The following GET request to is made to a resource that has a `307` redirection in place.
The Location header provides the URL of the redirected resource.

```http
GET /en-US/docs/AJAX HTTP/2
Host: developer.mozilla.org
User-Agent: curl/8.6.0
Accept: */*
```

```http
HTTP/2 307
location: /en-US/docs/Learn_web_development/Core/Scripting/Network_requests
content-type: text/plain; charset=utf-8
date: Fri, 19 Jul 2024 12:57:17 GMT
```
