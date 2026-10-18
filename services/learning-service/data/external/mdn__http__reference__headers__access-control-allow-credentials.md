<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Allow-Credentials -->
# Access-Control-Allow-Credentials header

The HTTP **`Access-Control-Allow-Credentials`** response header tells browsers whether the server allows credentials to be included in cross-origin HTTP requests.

Credentials include cookies, Transport Layer Security (TLS) client certificates, or authentication headers containing a username and password.
By default, these credentials are not sent in cross-origin requests, and doing so can make a site vulnerable to Cross-Site Request Forgery (CSRF) attacks.

A client can ask for credentials to be included in cross-site requests in several ways:

- Using fetch(), by setting the `credentials` option to `"include"`.
- Using XMLHttpRequest, by setting the XMLHttpRequest.withCredentials property to `true`.
- Using EventSource(), by setting the EventSource.withCredentials property to `true`.

When credentials are included:

- For preflighted requests: The preflight request does not include credentials.
  If the server's response to the preflight request sets the `Access-Control-Allow-Credentials` header to `true`, then the real request will include credentials; otherwise, the browser reports a network error.
- For non-preflighted requests: The request will include credentials, and if the server's response does not set the `Access-Control-Allow-Credentials` header to `true`, the browser reports a network error.

      Header type
      Response header

## Syntax

```http
Access-Control-Allow-Credentials: true
```

## Directives

- `true`
  - : The server allows credentials to be included in cross-origin HTTP requests.
    This is the only valid value for this header and is case-sensitive.
    If you don't need credentials, omit this header entirely rather than setting its value to `false`.

## Examples

Allow credentials:

```http
Access-Control-Allow-Credentials: true
```

Using fetch() with credentials:

```js
fetch(url, {
  credentials: "include",
});
```

Using XMLHttpRequest with credentials:

```js
const xhr = new XMLHttpRequest();
xhr.open("GET", "http://example.com/", true);
xhr.withCredentials = true;
xhr.send(null);
```
