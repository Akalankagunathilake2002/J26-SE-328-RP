<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: Web Security -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Security/Practical_implementation_guides/CSP -->
# Content Security Policy (CSP) implementation

The `Content-Security-Policy` HTTP header provides fine-grained control over the code that can be loaded on a site, and what it is allowed to do.

## Problem

The main problem this article focuses on is cross-site scripting (XSS) attacks. These are generally due to a lack of control and awareness of the sources from which site resources are loaded. This problem gets more difficult to manage as sites become larger and more complex and increasingly rely on third-party resources such as JavaScript libraries.

> [!NOTE]
> CSP is one part of a complete strategy for protecting against XSS attacks. There are other factors involved, such as output encoding and sanitization, which are also important.

CSP can also help to fix other problems, which are covered in other articles:

- Preventing clickjacking by stopping your site being embedded into iframe elements. This is done using the CSP `frame-ancestors` directive.
- Preventing manipulator in the middle (MiTM) attacks by upgrading any HTTP connections to HTTPS. This is helped by the CSP `upgrade-insecure-requests` directive. See Upgrading insecure requests.

## Solution

Implementing a strict CSP is the best way to mitigate XSS vulnerabilities with CSP. This uses nonce- or hash-based fetch directives to ensure that only scripts and/or styles that include the correct nonce or hash will be executed. JavaScript inserted by a hacker will simply not run.

Strict CSPs also:

- Disable the use of unsafe inline JavaScript, meaning inline event handler attributes such as `onclick`. This prevents improperly-escaped user inputs from being interpreted by the web browser as JavaScript.
- Disable the use of risky API calls such as `eval()`, which is another effect of the `script-src` directive.
- Disable all object embeds via `object-src 'none'`.
- Disable uses of the `` element to set a base URI via `base-uri 'none';`.

Strict CSPs are preferred over location-based policies, also called allowlist policies, where you specify which domains scripts can be run from. This is because allowlist policies often end up allowing unsafe domains, which defeats the entire point of having a CSP, and they can get very large and unwieldy, especially if you are trying to permit services that require many third-party scripts to function.

### Steps for implementing CSP

Implement a strict CSP, then start to pinpoint resources that are failing to load as a result of the policy, taking steps to work around these issues.

> [!NOTE]
> Before implementing any actual CSP with the `Content-Security-Policy` header, you are advised to first test it out using the `Content-Security-Policy-Report-Only` HTTP header; see Report-only CSPs below.

1. Decide whether to use nonces or hashes. You should use nonces if you can dynamically generate content or hashes if you need to serve static content.
2. Implement a strict CSP, as outlined in the Solution section. Make sure that external and internal scripts (included via script elements) that you want to run have the correct nonce inserted into the `nonce` attributes by the server. If you are instead using hashes, external scripts should have the correct hash inserted into `integrity` attributes.
3. If an allowed script goes on to load third-party scripts, those scripts will fail to load because they won't have the required nonce or hash. Mitigate this problem by adding the `strict-dynamic` directive, which gives scripts loaded by the first script the same level of trust without being explicitly given a nonce or hash.
4. Refactor patterns disallowed by the strict CSP, such as inline event handlers and `eval()`. For example, replace inline event handlers with `addEventListener()` calls inside scripts.
5. Unless sites need the ability to include embeds, their execution should be disabled with `object-src 'none'`.
6. If you are unable to remove usages of `eval()`, you can add the `unsafe-eval` keyword to your strict CSP to allow them, although this makes the CSP significantly weaker.
7. If you are unable to remove event handler attributes, you can add the `unsafe-hashes` keyword to your strict CSP to allow them. This is somewhat unsafe, but much safer than allowing all inline JavaScript.

If you are unable to get a strict CSP to work, an allowlist-based CSP is much better than none, and a CSP like `default-src https:` still provides some protection, disabling unsafe inline/`eval()` and only allowing loading of resources (images, fonts, scripts, etc.) over HTTPS.

> [!WARNING]
> If at all possible, avoid including unsafe sources inside your CSP. Examples include:
>
> - `unsafe-inline`.
> - `data:` URIs inside `script-src`, `object-src`, or `default-src`.
> - Overly broad sources or form submission targets.

If you are unable to use the `Content-Security-Policy` header, pages can instead include a `` element. This should be the first meta element that appears inside the document head.

### Report-only CSPs

Before implementing any actual CSP with the `Content-Security-Policy` header, you are advised to first test it out using the `Content-Security-Policy-Report-Only` HTTP header. This allows you to see if any violations would have occurred with that policy.

Sites should use the `report-to` and `report-uri` reporting directives. These cause the browser to `POST` JSON reports about CSP violations to endpoints (specified in the Reporting-Endpoints header in the case of `report-to`). This allows CSP violations to be caught and repaired quickly.

> [!NOTE]
> The `report-to` directive is preferred over the deprecated `report-uri` directive. However, both are still needed because `report-to` does not yet have full cross-browser support.
