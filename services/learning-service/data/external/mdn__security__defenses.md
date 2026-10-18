<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: Web Security -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Security/Defenses -->
# Defenses

These pages describe web platform features that provide defenses against one or more security attacks.

As a rule, there's a many-to-many relationship between attacks and defenses. In each of our attacks guides we describe the specific defenses against that attack. In the defenses pages listed below, we provide a broader overview of these defenses and how they work.

- Certificate transparency
  - : Provides a publicly visible log of issued TLS certificates, making it easier to detect those which were malicious or incorrectly issued.
- Input validation
  - : Checking that input provided by the user is what the site expects.
- Mixed content blocking
  - : Prevents a document that was delivered over HTTPS from loading subresources (such as scripts, images, or fonts) over HTTP.
- Operational security
  - : Security practices that are concerned with the processes to follow in developing, building, shipping, and updating a project.
- Same-origin policy
  - : Restricts the ways in which content loaded from one origin can access content loaded from a different origin. It controls the extent to which websites can access each other's state.
- Secure contexts
  - : A secure context is a `Window` or `Worker` for which certain standards of authentication and confidentiality are met. This usually means that it was delivered over HTTPS. Code running in a secure context is able to use powerful web APIs that are not made available in insecure contexts.
- Subresource integrity
  - : Enables a website to verify that scripts and stylesheets loaded from an external source (such as a CDN) have the expected content, and have not been modified.
- Transport Layer Security (TLS)
  - : Enables a client to communicate securely with a server across an untrusted network. Most notably, on the web, it's used to secure HTTP connections: the resulting protocol is called HTTPS. HTTPS is the only real defense against Manipulator in the Middle (MITM) attacks.
- User activation
  - : To protect the user from potentially malicious websites, certain powerful APIs can only be used when the user meaning the user is currently interacting with the web page, or has interacted with the page at least once since it loaded.
- Local network access
  - : The local network access technology places restrictions on the ability of websites to make requests to the user's local network, mitigating the risk of attacks such as cross-site request forgeries. This article explains how local network access works, and what web developers need to do to interact with it.
