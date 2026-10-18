<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: Web Security -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Security -->
# Security

Web security is the practice of protecting websites and their users from damage caused by malicious third parties, who are generally called _attackers_.

The kind of damage done can be reputational, financial, or even physical. It can target data that should be kept private to users, or actions that should be only made available to particular users. The motivations of attackers might be financial, political, or personal.

In this part of MDN we've written guides to help web developers understand how to protect their websites, and their users, against these attacks.

The documentation is organized into four main sections:

- Attacks
- Defenses
- Threat modeling
- Authentication

In this page we'll introduce each of these sections and list the guides they contain. First though, we'll list the core security practices that web developers should follow.

## Core security practices

Web security can be overwhelming: there are a lot of potential threats, defenses are often complex and multilayered, and the set of threats you need to consider are highly dependent on what exactly your website is doing. In this section we'll summarize what we think are the most important things you can do, that will offer protection against most of the threats you will encounter.

- **Use HTTPS** to serve all your site's pages and subresources.

- **Set a Content Security Policy (CSP)** for your site.
  - If possible, set a strict CSP, but if not, at least set a policy that disallows inline JavaScript.
  - Set the `frame-ancestors` CSP directive, to control whether pages can be embedded in nested browsing contexts.

  - Set the `require-trusted-types-for` CSP directive, to help ensure that content has been sanitized before it is passed to potentially dangerous APIs.

- **Control cross-origin requests**: consider whether and in which circumstances you want to allow other origins to make requests to your site, and use fetch metadata to control this.

- **Limit access to any cookies your site sets**. In particular:
  - Set the `SameSite` attribute to `Strict` if possible, or `Lax` otherwise.
  - Set the `Secure` and `HttpOnly` attributes, if possible.
  - Minimize the lifetime of cookies that are used to represent logged-in users.

- **Handle input securely**: if your site accepts input from the user or another system, validate it. Before integrating any input into your site's pages, perform output encoding or sanitization.

- **Use Subresource Integrity** for any scripts that you load from external sources (such as CDNs).

- **Use strong authentication methods**: if you authenticate users on your site, don't use passwords alone. Passkeys are the most secure authentication method, but if you can't use them, then time-based one-time passwords (TOTP) are more secure than traditional passwords.

- **Follow good operational security practices**: control access to your project's source code, handle secrets securely, and control your dependencies.

See also the Secure Web Application Guidelines.

## Attacks

The Attacks section includes guides to common attacks on websites. An attack is a specific technique that an attacker can use to harm websites or their users.

Each guide covers a specific attack (or class of related attacks), explaining how it works, the conditions under which a website becomes vulnerable, and how to defend against it.

The attacks described include:

- Clickjacking
- Cross-site request forgery (CSRF)
- Cross-site leaks (XS-Leaks)
- Cross-site scripting (XSS)
- Insecure Direct Object Reference (IDOR)
- Manipulator in the Middle (MITM)
- Phishing
- Prototype pollution
- Server Side Request Forgery (SSRF)
- Subdomain takeover
- Supply chain attacks

## Defenses

The Defenses section includes guides to features or practices that you can use to protect yourself against various attacks. In general, there's a many-to-many relationship between attack and defenses. That is, a single defense can protect against multiple attacks, and defending against a single attack may require multiple defenses, so as to provide defense in depth.

In this section we document the following defenses:

- Certificate transparency
- Input validation
- Mixed content blocking
- Operational security
- Same-origin policy
- Secure contexts
- Subresource integrity
- Transport Layer Security (TLS)
- User activation

Note that not all defenses are described in this section: some, such as CSP or trusted types, are described inside the technology area of which they are a part.

## Threat modeling

Not all websites are vulnerable to all attacks: which attacks a developer needs to worry about depends on the features that the site provides and how they are implemented.

Threat modeling is a process that web developers can follow to develop a structured representation of the potential threats that their site faces, and the corresponding defenses that they should employ.

That is, threat modeling helps you understand which attacks you need to defend against, and how to defend against them.

## Authentication

Authentication is the process of verifying that an entity — such as a user of a website — is who they claim to be. You'll most likely need to think about authentication if you want users to sign into your website.

If users can log into your website, there are typically things logged-in users can do, or data they can access, that you don't want to make generally available. This makes user account access one of the most valuable targets for attackers.

In this set of guides we'll look at the main techniques available for authenticating users on the web, and good practices for them. We describe four methods:

- Passwords
- One-time passwords (OTP)
- Federated identity
- Passkeys

In this section we also outline good practices for session management, which is how a website remembers the signed-in status of a user.

## HTTP Observatory

The HTTP Observatory tool enables you to scan your website to check whether it's following certain good security practices. Our Practical security implementation guides provide explanations of how to implement these practices, and the threats they defend against.
