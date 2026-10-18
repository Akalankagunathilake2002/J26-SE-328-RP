<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Origin -->
# Origin header

The HTTP **`Origin`** request header indicates the origin (scheme, hostname, and port) that _caused_ the request.
For example, if a user agent needs to request resources included in a page, or fetched by scripts that it executes, then the origin of the page may be included in the request.

      Header type
      Request header

      Forbidden request header
      Yes

## Syntax

```http
Origin: null
Origin: ://
Origin: ://:
```

## Directives

- `null`
  - : The origin is "privacy sensitive", or is an opaque origin (specific cases are listed in the description section).
- ``
  - : The protocol that is used.
    Usually, it is the HTTP protocol or its secured version, HTTPS.
- ``
  - : The domain name or the IP address of the origin server.
- ``
  - : Port number on which the server is listening.
    If no port is given, the default port for the requested service is implied from the scheme (e.g., `80` for an HTTP URL).

## Description

The `Origin` header is similar to the Referer header, but does not disclose the path, and may be `null`.
It is used to provide the security context for the origin request, except in cases where the origin information would be sensitive or unnecessary.

Broadly speaking, user agents add the `Origin` request header to:

- cross origin requests.
- same-origin requests except for GET or HEAD requests (i.e., they are added to same-origin POST, OPTIONS, PUT, PATCH, and DELETE requests).

There are some exceptions to the above rules; for example, if a cross-origin GET or HEAD request is made in no-cors mode, the `Origin` header will not be added.

The `Origin` header value may be `null` in a number of cases, including (non-exhaustively):

- Origins whose scheme is not one of `http`, `https`, `ftp`, `ws`, `wss`, or `gopher` (including `blob`, `file` and `data`).
- Cross-origin images and media data, including that in img, video and audio elements.
- Documents created programmatically using createDocument(), generated from a `data:` URL, or that do not have a creator browsing context.
- Redirects across origins.
- Documents served with the Content-Security-Policy `sandbox` directive whose value doesn't include `allow-same-origin`.
- iframes with a sandbox attribute whose value doesn't include `allow-same-origin`.
- Responses that are network errors.
- Certain Referrer-Policy values, for requests that use neither `GET` nor `HEAD` and aren't made in `cors` mode (e.g., basic form posts).
  See Effect on the `Origin` header for the policy values that trigger this.

> [!NOTE]
> There is a more detailed listing of cases that may return `null` on Stack Overflow: When do browsers send the Origin header? When do browsers set the origin to null?

## Examples

```http
Origin: https://developer.mozilla.org
```

```http
Origin: https://developer.mozilla.org:80
```
