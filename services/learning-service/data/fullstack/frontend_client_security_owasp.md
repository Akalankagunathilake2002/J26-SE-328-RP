# Client-Side Security: Defending Against XSS, CSRF, and Supply Chain Vulnerabilities

## Cross-Site Scripting (XSS)
XSS occurs when an application includes untrusted user input into its rendered DOM without sanitization, allowing an attacker to execute arbitrary JavaScript in the victim's browser session.

### XSS Variants
1. **Stored XSS**: Malicious script is saved in the database (e.g. comment field) and served to all subsequent viewers.
2. **Reflected XSS**: Malicious payload is reflected immediately off a URL query parameter into an error message or search page.
3. **DOM-based XSS**: Vulnerability entirely within client-side code where unsafe sinks (`innerHTML`, `eval()`, `document.write()`) ingest user sources (`window.location.hash`).

### Defenses Against XSS
- Context-aware HTML entity encoding and DOM sanitization via libraries like DOMPurify.
- React/JSX automatic string escaping by default (never using `dangerouslySetInnerHTML` on untrusted input).
- **Content Security Policy (CSP)**: An HTTP response header specifying authorized domains for script execution, inline style restrictions, and banning `eval()`.
  ```http
  Content-Security-Policy: default-src 'self'; script-src 'self' https://trustedscripts.com; object-src 'none';
  ```

## Cross-Site Request Forgery (CSRF)
CSRF tricks an authenticated victim into submitting an unauthorized state-changing request (e.g. transfer money or change email) to a vulnerable target web application that relies solely on ambient browser session cookies.

### Defenses Against CSRF
- **`SameSite` Cookie Attribute**: Setting `SameSite=Strict` or `SameSite=Lax` on session cookies instructs the browser not to send cookies on cross-origin requests.
- **Anti-CSRF Tokens (Synchronizer Token Pattern)**: A cryptographically random secret token bound to the user session, embedded in form payloads or custom headers (`X-CSRF-Token`).
- **Custom Request Headers**: Requiring custom headers (`X-Requested-With` or `Authorization: Bearer <jwt>`) prevents standard HTML form submissions, forcing a preflight `OPTIONS` check.

## Secure Storage of Authentication Credentials
- **Local Storage / Session Storage Vulnerability**: Any JavaScript running on the origin (including through XSS or third-party npm supply chain attacks) can read `localStorage.getItem('token')`.
- **`HttpOnly` Cookie Standard**: Storing access tokens in `HttpOnly; Secure; SameSite=Strict` cookies makes them completely inaccessible to client JavaScript APIs, preventing token theft via XSS.
