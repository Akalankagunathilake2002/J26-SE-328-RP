<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Modified-Since -->
# If-Modified-Since header

The HTTP **`If-Modified-Since`** request header makes a request conditional.
The server sends back the requested resource, with a 200 status, only if it has been modified after the date in the `If-Modified-Since` header.
If the resource has not been modified since, the response is a 304 without any body, and the Last-Modified response header of the previous request contains the date of the last modification.

Unlike If-Unmodified-Since, `If-Modified-Since` can only be used with a GET or HEAD.
When used in combination with If-None-Match, it is ignored, unless the server doesn't support `If-None-Match`.

The most common use case is to update a cached entity that has no associated ETag.

      Header type
      Request header

      Forbidden request header
      No

## Syntax

```http
If-Modified-Since: ,    :: GMT
```

## Directives

- ``
  - : One of `Mon`, `Tue`, `Wed`, `Thu`, `Fri`, `Sat`, or `Sun` (case-sensitive).
- ``
  - : 2 digit day number, e.g., "04" or "23".
- ``
  - : One of `Jan`, `Feb`, `Mar`, `Apr`, `May`, `Jun`, `Jul`, `Aug`, `Sep`, `Oct`, `Nov`, `Dec` (case sensitive).
- ``
  - : 4 digit year number, e.g., "1990" or "2016".
- ``
  - : 2 digit hour number, e.g., "09" or "23".
- ``
  - : 2 digit minute number, e.g., "04" or "59".
- ``
  - : 2 digit second number, e.g., "04" or "59".
- GMT
  - : Greenwich Mean Time. HTTP dates are always expressed in GMT, never in local time.

## Examples

```http
If-Modified-Since: Wed, 21 Oct 2015 07:28:00 GMT
```
