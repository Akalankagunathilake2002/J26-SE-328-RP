<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Guides -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP/Errors/CSPViolation -->
# Content Security Policy: The page's settings blocked the loading of a resource: xyz

The warning "Content Security Policy: The page's settings blocked the loading of a resource: xyz" occurs when the page's CSP configuration given by `xyz` prevents the resource from being loaded into the document's context.

## Message

### Firefox

`Content Security Policy: The pages settings blocked the loading of a resource: xyz`

with:

- `xyz`
  - : The name of the CSP directive that blocked the resource. This may be expressed as either just the name of the directive, or as the entire policy directive string.
- `uvw`
  - : Text that provides information that may help you resolve the problem, potentially including specific changes you might make to the CSP configuration.

### Chrome

- `Refused to apply inline style because it violates the following Content Security Policy Directive: "xyz". uvw.`
- `Refused to execute inline script because it violates the following Content Security Policy directive: "xyz". uvw.`
- `Refused to run the JavaScript URL because it violates the following Content Security Policy directive: "xyz". uvw.`
- `Refused to execute inline event handler because it violates the following Content Security Policy directive: "xyz". uvw.`

with:

- `xyz`
  - : The name of the CSP directive that blocked the resource. This may be expressed as either just the name of the directive, or as the entire policy directive string.
- `uvw`
  - : Text that provides information that may help you resolve the problem, potentially including specific changes you might make to the CSP configuration.

## What went wrong?

This warning message means that due to the existence of a particular CSP directive, a resource wasn't loaded.
