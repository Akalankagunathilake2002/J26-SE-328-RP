<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/103 -->
# 103 Early Hints

The HTTP **`103 Early Hints`** informational response may be sent by a server while it is still preparing a response, with hints about the sites and resources that the server expects the final response will link to.
This allows a browser to preconnect to sites or start preloading resources even before the server has prepared and sent a final response.
Preloaded resources indicated by early hints are fetched by the client as soon as the hints are received.

The early hint response is primarily intended for use with the Link header, which indicates the resources to be loaded.
It may also contain a `Content-Security-Policy` header that is enforced while processing the early hint.

A server might send multiple `103` responses, for example, following a redirect.
Browsers only process the first early hints response, and this response must be discarded if the request results in a cross-origin redirect.

> [!NOTE]
> For compatibility and security reasons, it is recommended to only send HTTP `103 Early Hints` responses over HTTP/2 or later unless the client is known to handle informational responses correctly.
>
> Most browsers limit support to HTTP/2 or later for this reason. See browser compatibility below.
> Despite this, the examples below use HTTP/1.1-style notation as per usual convention.

## Syntax

```http
103 Early Hints
```

## Examples

### Preconnect example

The following `103` early hint response shows an early hint response where the server indicates that the client might want to preconnect to a particular origin (`https://cdn.example.com`).
Just like the HTML `rel=preconnect` attribute, this is a hint that the page is likely to need resources from the target resource's origin, and that the browser may improve the user experience by preemptively initiating a connection to that origin.

```http
103 Early Hint
Link: ; rel=preconnect, ; rel=preconnect; crossorigin
```

This example preconnects to `https://cdn.example.com` twice:

- The first connection would be used for loading resources that can be fetched without CORS, such as images.
- The second connection includes the `crossorigin` attribute and would be used for loading CORS-protected resources, such as fonts.

CORS-protected resources must be fetched over a completely separate connection. If you only need one type of resource from an origin then you only need to preconnect once.

Subsequently the server sends the final response.
This includes a crossorigin font preload and an `` loaded from the additional origin.

```http
200 OK
Content-Type: text/html

...

...

...
```

### Preload example

The following `103` early hint response indicates a stylesheet `style.css` might be needed by the final response.

```http
103 Early Hint
Link: ; rel=preload; as=style
```

Subsequently the server sends the final response.
This includes a link to the stylesheet, which may already have been preloaded from the early hint.

```http
200 OK
Content-Type: text/html

...

...
```

### Early hint response with CSP

The following example shows the same early hint response but with a `Content-Security-Policy` header included.

```http
103 Early Hint
Content-Security-Policy: style-src: self;
Link: ; rel=preload; as=style
```

The early response restricts preloading to the same origin as the request.
The stylesheet will be preloaded if the origin matches.

The final response might set the CSP to `none`, as shown below.
The stylesheet has already been preloaded, but will not be used when rendering the page.

```http
200 OK
Content-Security-Policy: style-src: none;
Content-Type: text/html

...

...
```
