<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Methods -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/TRACE -->
# TRACE request method

The **`TRACE`** HTTP method performs a message loop-back test along the path to the target resource.

The final recipient of the request should reflect the message as received (excluding any fields that might include sensitive data) back to the client as the message body of a 200 OK response with a Content-Type of `message/http`.
The final recipient is either the origin server or the first server to receive a Max-Forwards value of `0` in the request.

The client must not send content in the request, or generate headers that might include sensitive data such as user credentials or cookies.
Not all servers implement the `TRACE` method, and some server owners have historically disallowed the use of the `TRACE` method due to security concerns.
In such cases, a 405 Method Not Allowed client error response will be sent.

      Request has body
      No

      Successful response has body
      Yes

      Safe
      Yes

      Idempotent
      Yes

      Cacheable
      No

      Allowed in HTML forms
      No

## Syntax

```http
TRACE ["?"] HTTP/1.1
```

- ``
  - : Identifies the target resource of the request when combined with the information provided in the Host header.
    This is an absolute path (e.g., `/path/to/file.html`) in requests to an origin server, and an absolute URL in requests to proxies (e.g., `http://www.example.com/path/to/file.html`).
- ``
  - : An optional query component preceded by a question-mark `?`.
    Often used to carry identifying information in the form of `key=value` pairs.

## Examples

### Successful TRACE request

A `TRACE` request can be performed using `curl`:

```bash
curl -v -X TRACE example.com
```

This produces the following HTTP request:

```http
TRACE / HTTP/1.1
Host: example.com
User-Agent: curl/8.7.1
Accept: */*
```

A 200 OK response with the request headers contained in response body is sent back to the client:

```http
HTTP/1.1 200 OK
Content-Length: 123
Date: Wed, 04 Sep 2024 11:50:24 GMT
Server: Apache/2.4.59 (Unix)
Content-Type: message/http

TRACE / HTTP/1.1
Host: example.com
User-Agent: curl/8.7.1
Accept: */*
```
