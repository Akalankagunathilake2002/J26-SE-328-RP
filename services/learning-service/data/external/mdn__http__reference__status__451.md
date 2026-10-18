<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/451 -->
# 451 Unavailable For Legal Reasons

The HTTP **`451 Unavailable For Legal Reasons`** client error response status code indicates that the user requested a resource that is not available due to legal reasons, such as a web page for which a legal action has been issued.

## Status

```http
451 Unavailable For Legal Reasons
```

## Examples

### Response with Link header

This example response is taken from the IETF RFC (see below) and contains a reference to Monty Python's Life of Brian.

> [!NOTE]
> The Link header might also contain a `rel="blocked-by"` relation identifying the entity implementing the blockage, not any other entity mandating it.

Any attempt to identify the entity ultimately responsible for the resource being unavailable belongs in the response body, not in the `rel="blocked-by"` link. This includes the name of the person or organization that made a legal demand resulting in the content's removal.

```http
HTTP/1.1 451 Unavailable For Legal Reasons
Link: ; rel="blocked-by"
Content-Type: text/html

      Unavailable For Legal Reasons

            Unavailable For Legal Reasons
            This request may not be serviced in the Roman Province
            of Judea due to the Lex Julia Majestatis, which disallows
            access to resources hosted on servers deemed to be
            operated by the People's Front of Judea.

```
