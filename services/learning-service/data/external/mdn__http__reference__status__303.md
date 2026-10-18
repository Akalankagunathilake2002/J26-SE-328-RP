<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/303 -->
# 303 See Other

The HTTP **`303 See Other`** redirection response status code indicates that the browser should redirect to the URL in the Location header instead of rendering the requested resource.

This response code is often sent back as a result of PUT or POST methods so the client may retrieve a confirmation, or view a representation of a real-world object (see HTTP range-14).
The method to retrieve the redirected resource is always GET.

## Status

```http
303 See Other
```

## Examples

### 303 response on form submission

The client in this example sends a POST request to submit a form to a generic subscription.

```http
POST /subscribe HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded
Content-Length: 50

name=Brian%20Smith&email=brian.smith%40example.com
```

The server may send back a response with a `303` status and a confirmation page in the Location header, so the user is redirected there after receiving the response.

```http
HTTP/1.1 303 See Other
Location: https://www.example.com/confirmation/event/123
Content-Type: text/html; charset=UTF-8
Content-Length: 0
```
