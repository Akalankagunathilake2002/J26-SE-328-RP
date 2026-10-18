<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/408 -->
# 408 Request Timeout

The HTTP **`408 Request Timeout`** client error response status code indicates that the server would like to shut down this unused connection.
A `408` is sent on an idle connection by some servers, _even without any previous request by the client_.

A server should send the Connection: close header field in the response, since `408` implies that the server has decided to close the connection rather than continue waiting.

This response is used much more since some browsers, like Chrome and Firefox, use HTTP pre-connection mechanisms to speed up surfing.

> [!NOTE]
> Some servers will shut down a connection without sending this message.

## Status

```http
408 Request Timeout
```

## Examples

### Timeout in form submission

The following example shows what a client may send when an `` element uses an image on form submission with `method="post"`:

```http
POST /upload HTTP/1.1
Host: example.com
Content-Type: multipart/form-data; boundary=----Boundary1234
Content-Length: 4012345

------Boundary1234
Content-Disposition: form-data; name="file"; filename="myImage.jpg"
Content-Type: image/jpeg

\xFF\xD8\xFF\xE0\x00...(binary data)
------Boundary1234--
```

If the data is not received in full due to network issues or latency, the server may timeout the connection.
Clients may repeat the request again, and a new connection will be used:

```http
HTTP/1.1 408 Request Timeout
Content-Type: text/html

    408 Request Timeout

    408 Request Timeout
    Failed to process request in time. Please try again.

```
