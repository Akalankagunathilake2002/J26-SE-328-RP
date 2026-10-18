<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: Web Security -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Security/Practical_implementation_guides/MIME_types -->
# MIME type verification

The `X-Content-Type-Options` header informs browsers not to load scripts and stylesheets unless the server indicates the correct MIME type.

## Problem

Without proper MIME type verification, browsers might incorrectly detect non-script and non-stylesheet files as scripts or stylesheets. This error allows potentially malicious files to be loaded via script and link elements as part of Cross-site scripting (XSS) attacks.

## Solution

All sites must set the `X-Content-Type-Options` header with a value of `nosniff`, and set appropriate MIME types for the files they serve (i.e., via the `Content-Type` header).

`nosniff` blocks a request if the request destination:

- is of type `style` and the MIME type is not `text/css`.
- is of type `script` and the MIME type is not a valid JavaScript MIME type.

## Examples

Prevent browsers from incorrectly detecting non-stylesheets as stylesheets and non-scripts as scripts:

```http
X-Content-Type-Options: nosniff
```
