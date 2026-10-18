<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Guides -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSExternalRedirectNotAllowed -->
# Reason: CORS request external redirect not allowed

## Reason

```plain
Reason: CORS request external redirect not allowed
```

## What went wrong?

The CORS request was responded to by the server with an HTTP redirect
to a URL on a different origin than the original request, which is not permitted during
CORS requests.

For example, if the page `https://service.tld/fetchdata` were requested, and
the HTTP response is "301 Moved Permanently", "307 Temporary Redirect", or "308
Permanent Redirect" with a `Location` of
`https://anotherservice.net/getdata`, the CORS request will fail in this
manner.

To fix the problem, update your code to use the new URL as reported by the redirect,
thereby avoiding the redirect.
