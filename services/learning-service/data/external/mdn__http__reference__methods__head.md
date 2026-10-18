<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Methods -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/HEAD -->
# HEAD request method

The **`HEAD`** HTTP method requests the metadata of a resource in the form of headers that the server would have sent if the GET method was used instead.
This method can be used in cases where a URL might produce a large download, for example, a `HEAD` request can read the Content-Length header to check the file size before downloading the file with a `GET`.

If the response to a `HEAD` request shows that a cached URL response is now outdated, the cached copy is invalidated even if no `GET` request was made.

> [!WARNING]
> If a response to a `HEAD` request has a body, the response body must be ignored.
> Any representation headers that describe the erroneous body are assumed to describe the response body that a `GET` request would have received.

      Request has body
      No

      Successful response has body
      No

      Safe
      Yes

      Idempotent
      Yes

      Cacheable
      Yes

        Allowed in HTML forms

      No

## Syntax

```http
HEAD ["?"] HTTP/1.1
```

- ``
  - : Identifies the target resource of the request when combined with the information provided in the Host header.
    This is an absolute path (e.g., `/path/to/file.html`) in requests to an origin server, and an absolute URL in requests to proxies (e.g., `http://www.example.com/path/to/file.html`).
- ``
  - : An optional query component preceded by a question-mark `?`.
    Often used to carry identifying information in the form of `key=value` pairs.

## Examples

### Successfully retrieving resource metadata

The following `curl` command creates a `HEAD` request for `example.com`:

```bash
curl --head example.com
```

This is the equivalent to a `GET` request, except the server shouldn't include a message body in the response.
It creates an HTTP request that looks like this:

```http
HEAD / HTTP/1.1
Host: example.com
User-Agent: curl/8.6.0
Accept: */*
```

The server sends back a 200 OK response comprised only of headers.
The response is effectively metadata that describes the resource instead of the resource itself (some caching headers are omitted in this example for brevity):

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Date: Wed, 04 Sep 2024 10:33:11 GMT
Content-Length: 1234567
```
