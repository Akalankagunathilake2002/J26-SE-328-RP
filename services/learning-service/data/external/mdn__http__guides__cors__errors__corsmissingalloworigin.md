<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Guides -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSMissingAllowOrigin -->
# Reason: CORS header 'Access-Control-Allow-Origin' missing

## Reason

```plain
Reason: CORS header 'Access-Control-Allow-Origin' missing
```

## What went wrong?

The response to the CORS request is missing the required
Access-Control-Allow-Origin header, which is used to determine whether
or not the resource can be accessed by content operating within the current origin.

If the server is under your control, add the origin of the requesting site to the set
of domains permitted access by adding it to the `Access-Control-Allow-Origin`
header's value.

For example, to allow a site at `https://example.com` to access the resource using CORS,
the header should be:

```http
Access-Control-Allow-Origin: https://example.com
```

You can also configure a site to allow any site to access it by using the
`*` wildcard. You should only use this for public APIs. Private APIs should
never use `*`, and should instead have a specific domain or domains set. In
addition, the wildcard only works for requests made with the
`crossorigin` attribute set to `anonymous`, and it prevents
sending credentials like cookies in requests.

```http
Access-Control-Allow-Origin: *
```

> [!WARNING]
> Using the wildcard to allow all sites to access a private
> API is a bad idea.

To allow any site to make CORS requests _without_ using the `*`
wildcard (for example, to enable credentials), your server must read the value of the
request's `Origin` header and use that value to set
`Access-Control-Allow-Origin`, and must also set a `Vary: Origin`
header to indicate that some headers are being set dynamically depending on the origin.

## Examples for common web servers

The exact directive for setting headers depends on your web server.

In the examples below,

In **Apache** (docs), add a
line such as the following to the server's configuration (within the appropriate
``, ``,
``, or `` section). The
configuration is typically found in a `.conf` file (`httpd.conf`
and `apache.conf` are common names for these), or in an
`.htaccess` file:

```apacheconf
Header set Access-Control-Allow-Origin 'https://example.com'
```

For **Nginx** (docs), the command to set up this header is:

```nginx
add_header 'Access-Control-Allow-Origin' 'https://example.com' always;
```

## If you don't control the server

If the remote server is not under your control and does not include the `Access-Control-Allow-Origin` header, you cannot fix this error on the server side. Consider these alternatives:

- Restructure your request as a simple request to avoid triggering a preflight, if the server handles simple cross-origin requests.
- If you don't need to read the response, use `mode: "no-cors"` in your `fetch()` call. The response will be opaque (unreadable), but the request will succeed.
- Route the request through a proxy server you control, which fetches the resource and returns it with appropriate CORS headers.

See Client-side considerations for more detail.
