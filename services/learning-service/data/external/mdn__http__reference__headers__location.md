<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Location -->
# Location header

The HTTP **`Location`** response header indicates the URL to redirect a page to.
It only provides a meaning when served with a `3XX` redirection response or a 201 Created status response.

In redirections, the HTTP method used to make the redirected request to fetch the page pointed to by `Location` depends on the original method and the kind of redirection:

- 303 See Other responses always result in a GET request in the redirection.
- 307 Temporary Redirect and 308 Permanent Redirect use the same method as the initiating request.
- 301 Moved Permanently and 302 Found should use the same request method as the initiating request, although this is not guaranteed for older user-agents.

All responses with one of the above status codes include a `Location` header.

In cases of resource creation, it indicates the URL of the newly-created resource so that a client can make a request for it immediately.

`Location` and Content-Location are different.
`Content-Location` indicates the URL to use to directly access the resource in future when content negotiation occurred.
`Location` is associated with the response, while Content-Location is associated with the representation that was returned.

      Header type
      Response header

## Syntax

```http
Location:
```

## Directives

- ``
  - : May be relative to the request URL or an absolute URL.

## Examples

```http
Location: /index.html
```
