<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: Web Security -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Security/Practical_implementation_guides/CORS -->
# Cross-Origin Resource Sharing (CORS) configuration

Cross-Origin Resource Sharing (CORS) is handled using `Access-Control-Allow-Origin` and related headers. `Access-Control-Allow-Origin` defines the non-same origins that are allowed to make requests to pages on your domain (i.e., via `XMLHttpRequest` or `fetch()`).

## Problem

By default, same-origin policy blocks cross-origin HTTP requests initiated by scripts. There are several use cases that require cross-origin script access; for example, Content Delivery Networks (CDNs) that provide hosting for JavaScript/CSS libraries and public API endpoints. However, cross-origin access presents a major security risk and must be carefully controlled.

## Solution

Use `Access-Control-Allow-Origin` to define the non-same origins that are allowed to make requests to pages on your domain.

If present, `Access-Control-Allow-Origin` should specify the minimum possible number of origins and resources for your site to function. For example, if your server provides both a website and an API intended for remote `XMLHttpRequest` access, only the API resources should return the `Access-Control-Allow-Origin` header.

Failure to set `Access-Control-Allow-Origin` appropriately will allow unauthorized origins to read the contents of any page on your site. This can be especially dangerous if those sites are able to send credentials, potentially exposing your site to CSRF attacks.

If credentialed access is required from specific origins, ensure `Access-Control-Allow-Origin` is set only to those origins, rather than reflecting the `Origin` header. If public non-credentialed access is required, set `Access-Control-Allow-Origin` to `*` and omit the `Access-Control-Allow-Credentials` header. Otherwise, omit both headers.

## Examples

Allow any site to read the contents of a JavaScript library:

```http
Access-Control-Allow-Origin: *
```

> [!NOTE]
> This setting is required for Subresource integrity to work.

Allow `https://random-dashboard.example.org` to read the returned results of an API:

```http
Access-Control-Allow-Origin: https://random-dashboard.example.org
```
