<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/207 -->
# 207 Multi-Status

The HTTP **`207 Multi-Status`** successful response status code indicates a mixture of responses.
This response is used exclusively in the context of Web Distributed Authoring and Versioning (WebDAV).

The response body is a `text/xml` or `application/xml` HTTP entity with a `multistatus` root element that lists individual response codes.

> [!NOTE]
> Browsers accessing web pages will never encounter this status code.
> The ability to return a _collection of resources_ is part of the WebDAV protocol and is only encountered by web applications that access a WebDAV server.

## Status

```http
207 Multi-Status
```

## Examples

### Receiving a `207` response in a WebDAV context

The following response is an example `207` response that a WebDAV server sends to a client.
There is a `multistatus` root element with details of the individual collections:

```http
HTTP/1.1 207 Multi-Status
Content-Type: application/xml; charset="utf-8"
Content-Length: 1241

    http://www.example.com/Coll/

        Loop Demo

          urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf8

      HTTP/1.1 200 OK

    http://www.example.com/Coll/Bar

        Loop Demo

          urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf8

      HTTP/1.1 208 Already Reported

```
