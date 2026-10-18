<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: Web Security -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Security/Practical_implementation_guides/Cookies -->
# Secure cookie configuration

Limit access to cookies as much as possible.

## Problem

Cookies often contain session identifiers or other sensitive information. Unauthorized access to cookies, therefore, can cause a host of problems, including privacy issues, clickjacking attacks, cross-site request forgery (CSRF) attacks, and more.

## Solution

To minimize the scope for cookie vulnerabilities on your site, limit access to cookies as much as possible, by including the following cookie attributes when sending the `Set-Cookie` response header:

- `Name`
  - : Prepend cookie names with either `__Secure-` or `__Host-` to prevent cookies from being overwritten by insecure sources.
    - Use `__Host-` for all cookies needed only on a specific domain (no subdomains) where `Path` is set to `/`.
    - Use `__Secure-` for all other cookies.
- `Secure`
  - : Always set the `Secure` attribute, indicating that the cookie should only be sent over HTTPS.
- `HttpOnly`
  - : Set the `HttpOnly` attribute on all cookies that don't require access from JavaScript (for example, via Document.cookie).

    In particular, cookies that contain session identifiers should not have JavaScript access, to help prevent a cross-site scripting (XSS) attack from stealing session identifiers.

- `Expires` and `Max-Age`
  - : Cookies should expire as soon as they are no longer needed. Session identifiers in particular should expire as quickly as possible.
    - `Expires`: Sets an absolute expiration date for a given cookie.
    - `Max-Age`: Sets a relative expiration date for a given cookie.

      > [!NOTE]
      > `Expires` has been available for longer than `Max-Age`; however, `Max-Age` is less error-prone, and takes precedence when both are set. The rationale behind this is that when you set an `Expires` date and time, they're relative to the client on which the cookie is being set. If the server is set to a different time, this could cause errors.

      If neither `Expires` nor `Max-Age` are set, then the cookie is kept until the user closes their browser, and is then discarded.

- `Domain`
  - : Set the `Domain` attribute only if the cookie needs to be accessible on other domains, and in this case set it to the most restrictive domain possible.
- `Path`
  - : Set the most restrictive `Path` possible.
- `SameSite`
  - : Set the `SameSite` attribute to `Strict` or `Lax`, to restrict the transmission of cookies in requests that originate from a different site.

    This is a partial defense against CSRF, clickjacking, and some cross-site leak attacks.

## Examples

Set a session identifier cookie that is only accessible on the current host and expires when the user closes their browser:

```http
Set-Cookie: MOZSESSIONID=980e5da39d4b472b9f504cac9; Path=/; Secure; HttpOnly
```

Use the `__Secure-` prefix to set a session identifier for all `example.org` sites, set to expire after 30 days. This cookie is not included in most cross-site requests, but is included in navigations to your site from another site, such as by clicking a link:

```http
Set-Cookie: __Secure-MOZSESSIONID=7307d70a86bd4ab5a00499762; Max-Age=2592000; Domain=example.org; Path=/; Secure; HttpOnly; SameSite=Lax
```

Set a long-lived cookie for the current host, accessible by JavaScript, when the user accepts the terms of service. This cookie is not included in most cross-site requests, but is included in navigations to your site from another site, such as by clicking a link:

```http
Set-Cookie: __Host-ACCEPTEDTOS=true; Expires=Fri, 31 Dec 9999 23:59:59 GMT; Path=/; Secure; SameSite=Lax
```

Set a cookie containing a session identifier. It isn't sent from any cross-site requests, including navigations to your site from another site:

```http
Set-Cookie: __Host-BMOSESSIONID=YnVnemlsbGE=; Max-Age=2592000; Path=/; Secure; HttpOnly; SameSite=Strict
```
