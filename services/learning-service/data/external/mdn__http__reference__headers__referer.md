<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Referer -->
# Referer header

The HTTP **`Referer`** request header contains the absolute or partial address from which a resource has been requested.
The `Referer` header allows a server to identify referring pages that people are visiting from or where requested resources are being used.
This data can be used for analytics, logging, optimized caching, and more.

When you click a link, the `Referer` contains the address of the page that includes the link.
When you make resource requests to another domain, the `Referer` contains the address of the page that uses the requested resource.

The `Referer` header can contain an _origin_, _path_, and _querystring_, and may not contain URL fragments (i.e., `#section`) or `username:password` information.
The request's _referrer policy_ defines the data that can be included. See Referrer-Policy for more information and examples.

The `Referer` should also be sent in requests following a Refresh response (or equivalent ``) that causes a navigation to a new page, if permitted by the referrer policy.

> [!NOTE]
> The header name "referer" is actually a misspelling of the word "referrer".
> See HTTP referer on Wikipedia for more details.

> [!WARNING]
> This header may have undesirable consequences for user security and privacy.
> See Referer header: privacy and security concerns for more information and mitigation hints.

      Header type
      Request header

      Forbidden request header
      Yes

## Syntax

```http
Referer:
```

## Directives

- ``
  - : An absolute or partial address of the web page that makes the request.
    URL fragments (i.e., `#section`) and user info (i.e., `username:password` in `https://username:password@example.com/foo/bar/`) are not included.
    Origin, path, and query string may be included, depending on the referrer policy.

## Examples

```http
Referer: https://developer.mozilla.org/en-US/docs/Web/JavaScript
Referer: https://example.com/page?q=123
Referer: https://example.com/
```
