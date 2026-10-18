<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/428 -->
# 428 Precondition Required

The HTTP **`428 Precondition Required`** client error response status code indicates that the server requires the request to be conditional.

Typically, a 428 response means that a required precondition header such as If-Match **is missing**.
When a precondition header does **not match** the server-side state, the response should be 412 Precondition Failed.

## Status

```http
428 Precondition Required
```

## Examples

### Missing precondition in request

A client has fetched a resource `my-document` from the server, updated it locally, and then tries to send the updated document back to the server:

```http
PUT /docs/my-document HTTP/1.1
Host: example.com
Content-Type: application/json

{
  […]
```

The server implementation requires that all PUT requests for the specific path or type of documents must be conditional and sends a 428 response:

```http
HTTP/1.1 428 Precondition Required
Date: Wed, 26 Jun 2024 12:00:00 GMT
Server: Apache/2.4.1 (Unix)
Content-Type: application/json

{
  "code": "MissingPrecondition",
  "message": "Updating documents requires a precondition header.",
}
```
