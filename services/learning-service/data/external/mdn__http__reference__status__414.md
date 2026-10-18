<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/414 -->
# 414 URI Too Long

The HTTP **`414 URI Too Long`** client error response status code indicates that a URI requested by the client was longer than the server is willing to interpret.

There are a few rare conditions when this error might occur:

- a client has improperly converted a POST request to a GET request with long query information,
- a client has descended into a loop of redirection (for example, a redirected URI prefix that points to a suffix of itself), or
- the server is under attack by a client attempting to exploit potential security holes.

Some systems implement `414 URI Too Long` as `414 Request-URI Too Large`.

## Status

```http
414 URI Too Long
```

## Examples

### Form submission using GET

In the following example, an HTML `` method accidentally uses `get` instead of `post`.
A large amount of form data is appended to the URL specified at the form's `action` attribute and is sent as a GET request:

```http
GET /search?feedback=it+was+the+best+of+times+it+was+the+worst+of+times… HTTP/1.1
Host: example.com
```

The particular server's URI length limit is reached with this request and a 414 is sent in response:

```http
HTTP/1.1 414 URI Too Long
Content-Type: text/html; charset=UTF-8
Date: Fri, 28 Jun 2024 11:40:58 GMT
Content-Length: 1234

  414 - URI Too Long

    414 - URI Too Long
    The URI provided was too long for the server to process.

```
