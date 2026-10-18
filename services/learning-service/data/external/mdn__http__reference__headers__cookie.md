<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cookie -->
# Cookie header

The HTTP **`Cookie`** request header contains stored HTTP cookies associated with the server (i.e., previously sent by the server with the Set-Cookie header or set in JavaScript using Document.cookie).

The `Cookie` header is optional and may be omitted if, for example, the browser's privacy settings block cookies.

      Header type
      Request header

      Forbidden request header
      Yes

## Syntax

```http
Cookie:
Cookie: name=value
Cookie: name=value; name2=value2; name3=value3
```

## Directives

- ``
  - : A list of name-value pairs in the form of `=`.
    Pairs in the list are separated by a semicolon and a space.

## Examples

### Sending cookies

```http
Cookie: PHPSESSID=298zf09hf012fh2; csrftoken=u32t4o3tb3gg43; _gat=1
```

### Cookies with the same name

Multiple cookies can have the same name if they were set with different `Path` or `Domain` attributes.
This includes the case where one cookie was set with a `Domain` attribute and the other without, even if they apply to the same host. If more than one matches a request, the browser can include all of them in the `Cookie` header.

Partitioned cookies are keyed on the top-level site as well, so cookies can have the same name if set by the same host in two different embedding contexts. See CHIPS.

For example, suppose separate responses from the same host set these cookies:

```http
Set-Cookie: theme=light; Path=/
Set-Cookie: theme=dark; Path=/docs
```

A request to `/docs` can contain both of them:

```http
Cookie: theme=dark; theme=light
```

The `Cookie` header does not include the cookies' attributes, and the cookie entries are unordered, so the server cannot determine their paths or domains from the header alone.
