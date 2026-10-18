<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Methods -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/GET -->
# GET request method

The **`GET`** HTTP method requests a representation of the specified resource.
Requests using `GET` should only be used to request data and shouldn't contain a body.

> [!NOTE]
> The semantics of sending a message body in `GET` requests are undefined.
> Some servers may reject the request with a 4XX client error response.

      Request has body
      No

      Successful response has body
      Yes

      Safe
      Yes

      Idempotent
      Yes

      Cacheable
      Yes

      Allowed in HTML forms
      Yes

## Syntax

```http
GET ["?"] HTTP/1.1
```

- ``
  - : Identifies the target resource of the request when combined with the information provided in the Host header.
    This is an absolute path (e.g., `/path/to/file.html`) in requests to an origin server, and an absolute URL in requests to proxies (e.g., `http://www.example.com/path/to/file.html`).
- ``
  - : An optional query component preceded by a question-mark `?`.
    Often used to carry identifying information in the form of `key=value` pairs.

## Examples

### Successfully retrieving a resource

The following `GET` request asks for the resource at `example.com/contact`:

```http
GET /contact HTTP/1.1
Host: example.com
User-Agent: curl/8.6.0
Accept: */*
```

The server sends back the resource with a 200 OK status code, indicating success:

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Date: Fri, 21 Jun 2024 14:18:33 GMT
Last-Modified: Thu, 17 Oct 2019 07:18:26 GMT
Content-Length: 1234

```
