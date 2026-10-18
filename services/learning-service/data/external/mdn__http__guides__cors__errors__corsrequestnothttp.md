<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Guides -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS/Errors/CORSRequestNotHttp -->
# Reason: CORS request not HTTP

## Reason

```plain
Reason: CORS request not HTTP
```

## What went wrong?

CORS requests may only use the HTTP or HTTPS URL scheme, but the URL specified by the request is of a different type.
This often occurs if the URL specifies a local file, using the `file:///` scheme.

To fix this problem, make sure you use HTTPS URLs when issuing requests involving CORS, such as fetch(), XMLHttpRequest, Web Fonts (`@font-face`), and WebGL textures, and XSL stylesheets.

### Loading a local file

Local files from the same directory and subdirectories were historically treated as being from the same origin.
This meant that a file and all its resources could be loaded from a local directory or subdirectory during testing, without triggering a CORS error.

Unfortunately this had security implications, as noted in this advisory: CVE-2019-11730.
Many browsers, including Firefox and Chrome, now treat all local files as having _opaque origins_ (by default).
As a result, loading a local file with included local resources will now result in CORS errors.

Developers who need to perform local testing should now set up a local server.
As all files are served from the same scheme and domain (`localhost`) they all have the same origin, and do not trigger cross-origin errors.

> [!NOTE]
> This change is in line with the URL specification, which leaves the origin behavior for files to the implementation, but recommends that file origins are treated as opaque if in doubt.
