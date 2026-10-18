<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Guides -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSMissingAllowHeaderFromPreflight -->
# Reason: missing token 'xyz' in CORS header 'Access-Control-Allow-Headers' from CORS preflight channel

## Reason

```plain
Reason: missing token 'xyz' in CORS header 'Access-Control-Allow-Headers' from CORS preflight channel
```

## What went wrong?

The `Access-Control-Allow-Headers` header is sent by the server to let the client know which headers it supports for CORS requests. The value of `Access-Control-Allow-Headers` should be a comma-delineated list of header names, such as `X-Custom-Information` or any of the standard but non-basic header names (which are always allowed).

This error occurs when attempting to preflight a header that is not expressly allowed (that is, it's not included in the list specified by the `Access-Control-Allow-Headers` header sent by the server). To fix this, the server needs to be updated so that it allows the indicated header, or you need to avoid using that header.

If the server is not under your control, see Client-side considerations for alternative approaches.
