<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Length -->
# Content-Length header

The HTTP **`Content-Length`** header indicates the size, in bytes, of the message body sent to the recipient.

`Content-Length` is limited in that the message size must be known up front, before sending the headers, which is a problem when content is dynamically generated or streamed.

- In HTTP/1.0, it is required.
- In HTTP/1.1, it could be replaced with Transfer-Encoding: chunked for responses sent out in parts as its size is calculated.
- In HTTP/2, `Content-Length` is redundant, because the content length may be inferred from DATA frames. It may still be included for backwards compatibility.

      Header type

        Request header,
        Response header,
        Content header

      Forbidden request header
      Yes

        CORS-safelisted response header

      Yes

## Syntax

```http
Content-Length:
```

## Directives

- ``
  - : The length in octets.
