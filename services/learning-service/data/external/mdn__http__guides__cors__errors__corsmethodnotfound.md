<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Guides -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSMethodNotFound -->
# Reason: Did not find method in CORS header 'Access-Control-Allow-Methods

## Reason

```plain
Reason: Did not find method in CORS header 'Access-Control-Allow-Methods'
```

## What went wrong?

The HTTP method being used by the CORS request is not included in the
list of methods specified by the response's
Access-Control-Allow-Methods header. This header specifies a
comma-delimited list of the HTTP methods which may be used when using CORS to access
the URL specified in the request; if the request is using any other method, this error
occurs.

For example, if the response includes:

```http
Access-Control-Allow-Methods: GET,HEAD,POST
```

Trying to use a PUT request will fail with this error.

Make sure your code only uses the permitted HTTP methods when accessing the service.

> [!NOTE]
> If the server includes any unrecognized or undefined method names in its `Access-Control-Allow-methods` header, a different error occurs: Reason: invalid token 'xyz' in CORS header 'Access-Control-Allow-Methods'.

If the server is not under your control, see Client-side considerations for alternative approaches.
