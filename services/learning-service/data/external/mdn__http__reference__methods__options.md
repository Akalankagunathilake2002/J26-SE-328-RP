<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Methods -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/OPTIONS -->
# OPTIONS request method

The **`OPTIONS`** HTTP method requests permitted communication options for a given URL or server.
This can be used to test the allowed HTTP methods for a request, or to determine whether a request would succeed when making a CORS preflighted request.
A client can specify a URL with this method, or an asterisk (`*`) to refer to the entire server.

      Request has body
      May*

      Successful response has body
      May

      Safe
      Yes

      Idempotent
      Yes

      Cacheable
      No

      Allowed in HTML forms
      No

\* Although an `OPTIONS` message with a request body is technically allowed, it has no defined semantics.
You may include a body in an `OPTIONS` message as long as you provide a valid Content-Type header, and when you know the server expects it, as behavior is implementation-specific.

## Syntax

```http
OPTIONS *|["?"] HTTP/1.1
```

The request target may be either in 'asterisk form' `*` indicating the whole server, or a request target as is common with other methods:

- `*`
  - : Indicates that the client wishes to request `OPTIONS` for the server as a whole, as opposed to a specific named resource of that server.
- ``
  - : Identifies the target resource of the request when combined with the information provided in the Host header.
    This is an absolute path (e.g., `/path/to/file.html`) in requests to an origin server, and an absolute URL in requests to proxies (e.g., `http://www.example.com/path/to/file.html`).
- ``
  - : An optional query component preceded by a question-mark `?`.
    Often used to carry identifying information in the form of `key=value` pairs.

## Examples

### Identifying allowed request methods

To find out which request methods a server supports, one can use the `curl` command-line program to issue an `OPTIONS` request:

```bash
curl -X OPTIONS https://example.org -i
```

This creates the following HTTP request:

```http
OPTIONS / HTTP/2
Host: example.org
User-Agent: curl/8.7.1
Accept: */*
```

The response contains an Allow header that holds the allowed methods:

```http
HTTP/1.1 204 No Content
Allow: OPTIONS, GET, HEAD, POST
Cache-Control: max-age=604800
Date: Thu, 13 Oct 2016 11:45:00 GMT
Server: EOS (lax004/2813)
```

### Preflighted requests in CORS

In CORS, a preflight request is sent with the `OPTIONS` method so that the server can respond if it is acceptable to send the request. In this example, we will request permission for these parameters:

- The Access-Control-Request-Method header sent in the preflight request tells the server that when the actual request is sent, it will have a POST request method.
- The Access-Control-Request-Headers header tells the server that when the actual request is sent, it will have the `X-PINGOTHER` and `Content-Type` headers.

```http
OPTIONS /resources/post-here/ HTTP/1.1
Host: bar.example
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-us,en;q=0.5
Accept-Encoding: gzip,deflate
Connection: keep-alive
Origin: https://foo.example
Access-Control-Request-Method: POST
Access-Control-Request-Headers: content-type,x-pingother
```

The server now can respond if it will accept a request under these circumstances. In this example, the server response says that:

- Access-Control-Allow-Origin
  - : The `https://foo.example` origin is permitted to request the `bar.example/resources/post-here/` URL via the following:
- Access-Control-Allow-Methods
  - : POST, GET, and `OPTIONS` are permitted methods for the URL. (This header is similar to the Allow response header, but used only for CORS.)
- Access-Control-Allow-Headers
  - : `X-PINGOTHER` and `Content-Type` are permitted request headers for the URL.
- Access-Control-Max-Age
  - : The above permissions may be cached for 86,400 seconds (1 day).

```http
HTTP/1.1 200 OK
Date: Mon, 01 Dec 2008 01:15:39 GMT
Server: Apache/2.0.61 (Unix)
Access-Control-Allow-Origin: https://foo.example
Access-Control-Allow-Methods: POST, GET, OPTIONS
Access-Control-Allow-Headers: X-PINGOTHER, Content-Type
Access-Control-Max-Age: 86400
Vary: Accept-Encoding, Origin
Keep-Alive: timeout=2, max=100
Connection: Keep-Alive
```

> [!NOTE]
> Both 200 OK and 204 No Content are permitted status codes, but some browsers incorrectly believe `204 No Content` applies to the resource and do not send a subsequent request to fetch it.
