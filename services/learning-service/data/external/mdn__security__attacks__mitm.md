<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: Web Security -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/MITM -->
# Manipulator in the Middle (MITM)

In a Manipulator in the Middle (MITM) attack, the attacker inserts themselves between two entities that are trying to communicating with each other.

On the web, an MITM attack generally takes place between the user's browser and the server, and enables the attacker to see and potentially modify any of the traffic exchanged over HTTP.

A common way for an attacker to execute an MITM attack is to set up a wireless access point in a public place, such as a cafe or an airport, and wait for a victim to connect to it. If a victim does connect, then the attacker will be able to read and modify any data exchanged between the user's browser and any sites they connect to.

## Defenses against MITM

The primary defense against MITM is to serve your site over HTTPS (HTTP over TLS). HTTPS prevents an attacker from reading traffic, or from modifying it in a predictable way.

You should serve all pages over HTTPS, not just pages that you consider especially sensitive.

The TLS guide describes the main issues to consider here. In particular:

- Use a secure TLS configuration.

- Implement server authentication.

- Serve all resources over TLS: not only HTML documents but all subresources such as scripts, stylesheets, images, and fonts.

- If you redirect HTTP requests to use HTTPS, implement strict transport security (HSTS).
