<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: Web Security -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/Supply_chain_attacks -->
# Supply chain attacks

A _software supply chain_ consists of all the software and tools used to create and maintain a software product. This includes not only the software developed for the product itself but all the software and tools used in its production.

In a supply chain attack, the attacker targets part of the product's supply chain in order to compromise the product itself.

The most obvious example here is a third-party library. If you use, for example, an npm package developed by a third party, it has the ability to compromise your site. It may do so deliberately, if it is malicious, or accidentally, if it contains inadvertent vulnerabilities of its own. Essentially, you have to trust your third-party dependencies as much as you trust your own code.

Less obviously, the same principle applies to all the tools you use in creating your software, including code editors, editor plugins, version control systems, build tools, and so on. Any of these tools could insert malicious or vulnerable code into your final software product, in the course of the transformations they apply.

In this document we'll outline practices to follow to secure your software supply chain. It's organized into two main sections:

- Securing your development environment: practices to help ensure your own code isn't compromised.
- Managing third-party dependencies: practices to help ensure that your dependencies are not compromised.

## Securing your development environment

One route for a supply chain attack is for an attacker to introduce vulnerabilities or malicious code directly into your own product. Typically, an attacker does this by compromising the account of a project maintainer, or by exploiting weaknesses in the developer tools used by maintainers.

Our guide to operational security describes practices to counter these threats, including:

- Requiring strong authentication for project maintainers
- Implementing role-based access control for project maintainers
- Evaluating the tools you use
- Securing your configuration

## Managing third-party dependencies

Third-party dependencies include not only libraries and frameworks that your code uses, but all third-party tools involved in the development process, including editors, IDEs, source control systems, package managers, and build tools.

Attackers can compromise your project by exploiting weaknesses in these dependencies. Our guide to operational security describes practices to counter these threats, including:

- Evaluating new dependencies
- Updating existing dependencies
- Maintaining a _Software Bill of Materials_ (SBOM)

Additionally, projects should use Subresource Integrity for scripts and stylesheets that are hosted by a third-party site.

### Using Subresource Integrity

Many websites include externally hosted scripts: most notably, but not exclusively, scripts that are served from a Content Delivery Network (CDN):

```html

```

This represents a risk to your supply chain: if an attacker can get control of the `cdn.example.org` domain, they can replace the script with a malicious script, and thus compromise your site.

External scripts, like other software dependencies, should be part of your SBOM, but an additional defense is to set the script's `integrity` attribute:

```html
<script
  src="https://cdn.example.org/library.js"
  integrity="sha256-d5f450f7ce715d827de27ca569e183f819d33c1e7601875fd61eccbc98f56c5b">
```

The value of this attribute contains a cryptographic hash of the script's contents. If the script has been modified by an attacker, then the browser will refuse to load it, and you will be protected.

This does add an extra maintenance burden: every time the source changes (for example, every time a new version is released) you must update the attribute's value in your code.

The link element also supports the `integrity` attribute, so you can (and should) use it for CSS stylesheets as well as scripts.

See Subresource Integrity for more details.

## Defense summary checklist

- Follow operational security practices to:
  - Secure your own development environment.
  - Limit the risk of any third-party dependencies.
- Use Subresource Integrity for externally referenced scripts and stylesheets.
