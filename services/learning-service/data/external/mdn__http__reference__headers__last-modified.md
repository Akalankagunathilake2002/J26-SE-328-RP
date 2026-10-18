<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Last-Modified -->
# Last-Modified header

The HTTP **`Last-Modified`** response header contains a date and time when the origin server believes the resource was last modified.
It is used as a validator in conditional requests (If-Modified-Since or If-Unmodified-Since) to determine if a requested resource is the same as one already stored by the client.
It is less accurate than an ETag for determining file contents, but can be used as a fallback mechanism if ETags are unavailable.

`Last-Modified` is also used by crawlers to adjust crawl frequency, by browsers in heuristic caching, and by content management systems (CMS) to display the time the content was last modified.

      Header type
      Response header, Representation header

      Forbidden request header
      No

        CORS-safelisted response header

      Yes

## Syntax

```http
Last-Modified: ,    :: GMT
```

## Directives

- ``
  - : One of "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", or "Sun" (case-sensitive).
- ``
  - : 2 digit day number, e.g., "04" or "23".
- ``
  - : One of "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec" (case-sensitive).
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
Last-Modified: Wed, 21 Oct 2015 07:28:00 GMT
```
