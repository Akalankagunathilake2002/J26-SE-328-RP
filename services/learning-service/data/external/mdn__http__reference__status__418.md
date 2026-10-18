<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/418 -->
# 418 I'm a teapot

The HTTP **`418 I'm a teapot`** status response code indicates that the server refuses to brew coffee because it is, permanently, a teapot.
A combined coffee/tea pot that is temporarily out of coffee should instead return 503.
This error is a reference to Hyper Text Coffee Pot Control Protocol defined in April Fools' jokes in 1998 and 2014.

While originally defined in RFC 2324 as an April Fools' joke, this status code was formally reserved in RFC 9110 due to its wide deployment as a joke, so it cannot be assigned any non-joke semantics for the foreseeable future.

Some websites use this response for requests they do not wish to handle, such as automated queries.

## Status

```http
418 I'm a teapot
```
