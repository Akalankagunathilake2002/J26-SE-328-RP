<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: Web Security -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Security/Practical_implementation_guides/CORP -->
# Cross-Origin Resource Policy (CORP) implementation

Cross-Origin Resource Policy (CORP) is set by the Cross-Origin-Resource-Policy response header, which lets websites and applications opt-in to protection against vulnerabilities related to certain cross-origin requests (such as those made by the script and img elements).

## Problem

Some side-channel hardware vulnerabilities (also known as Cross-site leaks, or XS-Leaks), such as Meltdown>) and Spectre>), exploit a race condition arising as part of speculative execution functionality of modern processors. This functionality is designed to improve performance but can be manipulated to disclose sensitive data.

## Solution

Use `Cross-Origin-Resource-Policy` to block `no-cors` cross-origin requests to given resources. As this policy is expressed via a response header, the actual request is not prevented. Instead, the browser prevents the result from being leaked by stripping out the response body.

The possible values are:

- `same-origin`
  - : Limits resource access to requests coming from the same origin. This is recommended for URLs that reply with sensitive user information or private APIs.
- `same-site`
  - : Limits resource access to requests coming from the same site. This is recommended for responses from origins whose functionality is shared across several other same-site origins. Examples include a company CDN that serves static resources, and a single sign-on (SSO) app that handles authentication.
- `cross-origin`
  - : Allows resources to be accessed by cross-origin requests. This is recommended only for responses from widely-used origins, such as public CDNs or widgets. This is the default value if `Cross-Origin-Resource-Policy` is not set.

Set the most restrictive value possible for your site.

If, in turn, your site requires access to cross-origin resources, opt into a better default by sending a Cross-Origin-Embedder-Policy header along with the associated requests. This will prevent loading of cross-origin resources that don't also explicitly send a `Cross-Origin-Resource-Policy: cross-origin` header.

## Examples

Instruct browsers to disallow cross-origin requests made in `no-cors` mode:

```http
Cross-Origin-Resource-Policy: same-origin
```

Instruct browsers to allow cross-origin resource access, including access to features with unthrottled timers (such as SharedArrayBuffer objects or Performance.now()):

```http
Cross-Origin-Resource-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

This also permits such resources to be embedded.
