<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/X-Frame-Options -->
# X-Frame-Options header

> [!NOTE]
> For more comprehensive options than offered by this header, see the frame-ancestors directive in a Content-Security-Policy header.

The HTTP **`X-Frame-Options`** response header can be used to indicate whether a browser should be allowed to render the document in a frame, iframe, embed or object. Sites can use this to avoid clickjacking attacks and some cross-site leaks, by ensuring that their content is not embedded into other sites.

If this header is not sent, and the website has not implemented any other mechanisms to restrict embedding (such as the frame-ancestors CSP directive), then the browser will allow other sites to embed this document.

      Header type
      Response header

## Syntax

```http
X-Frame-Options: DENY
X-Frame-Options: SAMEORIGIN
```

### Directives

- `DENY`
  - : The document cannot be loaded in any frame, regardless of origin (both same- and cross-origin embedding is blocked).
- `SAMEORIGIN`
  - : The document can only be embedded if all ancestor frames have the same origin as the page itself.
- `ALLOW-FROM origin`
  - : This is an obsolete directive. Modern browsers that encounter response headers with this directive will ignore the header completely. The Content-Security-Policy HTTP header has a frame-ancestors directive which you should use instead.

## Examples

> [!WARNING]
> Setting `X-Frame-Options` inside the meta element (e.g., ``) has no effect. `X-Frame-Options` is only enforced via HTTP headers, as shown in the examples below.

### Configuring Apache

To configure Apache to send the `X-Frame-Options` header for all pages, add this to your site's configuration:

```apacheconf
Header always set X-Frame-Options "SAMEORIGIN"
```

To configure Apache to set `X-Frame-Options` to `DENY`, add this to your site's configuration:

```apacheconf
Header set X-Frame-Options "DENY"
```

### Configuring Nginx

To configure Nginx to send the `X-Frame-Options` header, add this either to your http, server or location configuration:

```nginx
add_header X-Frame-Options SAMEORIGIN always;
```

You can set the `X-Frame-Options` header to `DENY` using:

```nginx
add_header X-Frame-Options DENY always;
```

### Configuring IIS

To configure IIS to send the `X-Frame-Options` header, add this to your site's `Web.config` file:

```xml

  …

  …

```

For more information, see the Microsoft support article on setting this configuration using the IIS Manager user interface.

### Configuring HAProxy

To configure HAProxy to send the `X-Frame-Options` header, add this to your front-end, listen, or backend configuration:

```plain
rspadd X-Frame-Options:\ SAMEORIGIN
```

Alternatively, in newer versions:

```plain
http-response set-header X-Frame-Options SAMEORIGIN
```

### Configuring Express

To set `X-Frame-Options` to `SAMEORIGIN` using Helmet add the following to your server configuration:

```js
import helmet from "helmet";

const app = express();
app.use(
  helmet({
    xFrameOptions: { action: "sameorigin" },
  }),
);
```
