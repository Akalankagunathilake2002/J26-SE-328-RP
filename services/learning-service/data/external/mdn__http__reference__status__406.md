<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/406 -->
# 406 Not Acceptable

The HTTP **`406 Not Acceptable`** client error response status code indicates that the server could not produce a response matching the list of acceptable values defined in the request's proactive content negotiation headers and that the server was unwilling to supply a default representation.

Proactive content negotiation headers include:

- Accept
- Accept-Encoding
- Accept-Language

A server may return responses that differ from the request's accept headers.
In such cases, a 200 response with a default resource that doesn't match the client's list of acceptable content negotiation values may be preferable to sending a 406 response.

If a server returns a 406, the body of the message should contain the list of available representations for the resource, allowing the user to choose, although no standard way for this is defined.

## Status

```http
406 Not Acceptable
```

## Examples

### Content type not available

The following request assumes that `www.example.com/docs/doc1` supports sending a document back as `application/rtf`:

```http
GET /docs/doc1 HTTP/1.1
Host: example.com
Accept: application/rtf;
```

In this example, the server implementation does not fallback to a default content type like `text/html` or `application/json`, but returns a 406 instead:

```http
HTTP/1.1 406 Not Acceptable
Date: Wed, 26 Jun 2024 12:00:00 GMT
Server: Apache/2.4.1 (Unix)
Content-Type: application/json

{
  "code": "UnsupportedType",
  "message": "Only 'text/html' or 'application/json' content types supported.",
}
```
