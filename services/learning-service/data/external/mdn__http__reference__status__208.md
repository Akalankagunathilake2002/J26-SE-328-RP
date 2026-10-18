<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/208 -->
# 208 Already Reported

The HTTP **`208 Already Reported`** successful response status code is used in a 207 Multi-Status response to save space and avoid conflicts.
This response is used exclusively in the context of Web Distributed Authoring and Versioning (WebDAV).

If the same resource is requested several times (for example, as part of a collection) with different paths, only the first one is reported with 200.
Responses for all other bindings will report with this `208` status code, so no conflicts are created and the response stays shorter.

> [!NOTE]
> The ability to _bind_ a resource to several paths is an extension to the WebDAV protocol (it may be received by web applications accessing a WebDAV server).
> Browsers accessing web pages will never encounter this status code.

## Status

```http
208 Already Reported
```

## Examples

### Receiving a `208` in a `207 Multi-Status` response

The following is a sample `207 Multi-Status` response from a WebDAV server, which includes a `208` response.
Notice the `208` in the last `` element, which indicates that the resource named `Loop Demo` has been reported earlier in the `207` response.

```http
HTTP/1.1 207 Multi-Status
Content-Type: application/xml; charset="utf-8"
Content-Length: 1241

    http://www.example.com/Coll/

        Loop Demo

          urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf8

      HTTP/1.1 200 OK

    http://www.example.com/Coll/Foo

        Bird Inventory

          urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf9

      HTTP/1.1 200 OK

    http://www.example.com/Coll/Bar

        Loop Demo

          urn:uuid:f81d4fae-7dec-11d0-a765-00a0c91e6bf8

      HTTP/1.1 208 Already Reported

```
