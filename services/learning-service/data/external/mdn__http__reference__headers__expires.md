<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Expires -->
# Expires header

The HTTP **`Expires`** response header contains the date/time after which the response is considered expired in the context of HTTP caching.

The value `0` is used to represent a date in the past, indicating the resource has already expired.

> [!NOTE]
> If there is a Cache-Control header with the `max-age` or `s-maxage` directive in the response, the `Expires` header is ignored.

      Header type
      Response header

        CORS-safelisted response header

      Yes

## Syntax

```http
Expires: ,    :: GMT
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
Expires: Wed, 21 Oct 2015 07:28:00 GMT
```
