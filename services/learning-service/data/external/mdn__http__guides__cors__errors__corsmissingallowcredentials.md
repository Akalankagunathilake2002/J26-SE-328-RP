<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Guides -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSMissingAllowCredentials -->
# Reason: expected 'true' in CORS header 'Access-Control-Allow-Credentials

## Reason

```plain
Reason: expected 'true' in CORS header 'Access-Control-Allow-Credentials'
```

## What went wrong?

The CORS request requires that the server permit the use of
credentials, but the server's Access-Control-Allow-Credentials
header's value isn't set to `true` to enable their use.

To fix this problem on the client side, revise the code to not request the use of
credentials.

- If using the Fetch API, make sure
  Request.credentials is `"omit"`.
- If the request is being issued using XMLHttpRequest, make sure you're
  not setting withCredentials to
  `true`.
- If using Server-sent events,
  make sure EventSource.withCredentials is `false` (it's the
  default value).

To eliminate this error by changing the server's configuration, adjust the server's
configuration to set the `Access-Control-Allow-Credentials` header's value to
`true`.
