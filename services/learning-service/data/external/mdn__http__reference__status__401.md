<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/401 -->
# 401 Unauthorized

The HTTP **`401 Unauthorized`** client error response status code indicates that a request was not successful because it lacks valid authentication credentials for the requested resource.
This status code is sent with an HTTP WWW-Authenticate response header that contains information on the authentication scheme the server expects the client to include to make the request successfully.

A `401 Unauthorized` is similar to the 403 Forbidden response, except that a 403 is returned when a request contains valid credentials, but the client does not have permissions to perform a certain action.

## Status

```http
401 Unauthorized
```

## Examples

### Unauthorized request to a protected API

The following GET request is made to a URL `www.example.com/admin` that expects credentials in an Authorization header:

```http
GET /admin HTTP/1.1
Host: example.com
```

The server responds with a 401 message and a WWW-Authenticate header indicating that the request must be authenticated and that `Bearer` auth (an access token) is the permitted authentication scheme:

```http
HTTP/1.1 401 Unauthorized
Date: Tue, 02 Jul 2024 12:18:47 GMT
WWW-Authenticate: Bearer
```
