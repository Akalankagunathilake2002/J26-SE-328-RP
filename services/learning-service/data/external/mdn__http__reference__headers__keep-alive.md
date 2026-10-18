<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Headers -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Keep-Alive -->
# Keep-Alive header

The HTTP **`Keep-Alive`** request and response header allows the sender to hint how a connection may be used in terms of a timeout and a maximum number of requests.

> [!NOTE]
> For `Keep-Alive` to have any effect, the message must also include a Connection: keep-alive header.

HTTP/1.0 closes the connection after each request/response interaction by default, so persistent connections in HTTP/1.0 must be explicitly negotiated.
Some clients and servers might wish to be compatible with previous approaches to persistent connections, and can do this with a `Connection: keep-alive` request header.
Additional parameters for the connection can be requested with the `Keep-Alive` header.

> [!WARNING]
> Connection-specific header fields such as Connection and `Keep-Alive` are prohibited in HTTP/2 and HTTP/3.
> Chrome and Firefox ignore them in HTTP/2 responses, but Safari conforms to the HTTP/2 specification requirements and does not load any response that contains them.

      Header type

        Request header,
        Response header

      Forbidden request header
      Yes

## Syntax

```http
Keep-Alive:
```

## Directives

- ``
  - : A comma-separated list of parameters, each consisting of an identifier and a value separated by the equal sign (`=`).
    The following identifiers are possible:
    - `timeout`
      - : An integer that is the time in seconds that the host will allow an idle connection to remain open before it is closed.
        A connection is idle if no data is sent or received by a host. A host may keep an idle connection open for longer than `timeout` seconds, but the host should attempt to retain a connection for at least `timeout` seconds.
    - `max`
      - : An integer that is the maximum number of requests that can be sent on this connection before closing it.
        Unless `0`, this value is ignored for non-pipelined connections as another request will be sent in the next response.
        An HTTP pipeline can use it to limit the pipelining.

## Examples

A response containing a `Keep-Alive` header:

```http
HTTP/1.1 200 OK
Connection: Keep-Alive
Content-Encoding: gzip
Content-Type: text/html; charset=utf-8
Date: Thu, 11 Aug 2016 15:23:13 GMT
Keep-Alive: timeout=5, max=200
Last-Modified: Mon, 25 Jul 2016 04:32:39 GMT
Server: Apache

(body)
```
