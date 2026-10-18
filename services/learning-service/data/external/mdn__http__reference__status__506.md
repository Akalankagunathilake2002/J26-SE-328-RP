<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/506 -->
# 506 Variant Also Negotiates

The HTTP **`506 Variant Also Negotiates`** server error response status code is returned during content negotiation when there is recursive loop in the process of selecting a resource.

Agent-driven content negotiation enables a client and server to collaboratively decide the best variant of a given resource when the server has multiple variants.
A server sends a `506` status code due to server misconfiguration that results in circular references when creating responses.

Lack of standardization of how clients automatically choose from responses, and the additional round-trips that slow down client-server interaction mean this mechanism is rarely used.
Server-driven content negotiation is far more common, where a server directly chooses the most appropriate resource for the client based on the request headers (Accept-Language, Accept, etc.).

## Status

```http
506 Variant Also Negotiates
```

## Examples

### Resource with variants

In the following example, a client requests a page in the `fr` locale using the Accept-Language header.
This can be performed using curl:

```bash
curl  -H "Negotiate: trans" -H "Accept-Language: fr;" http://example.com/index
```

This produces the following request:

```http
GET /index HTTP/1.1
Host: example.com
User-Agent: curl/8.7.1
Accept: */*
Negotiate: trans
Accept-Language: fr
```

Due to server misconfiguration, the variant response for `fr` points to a type map which itself causes transparent negotiation to be performed.
The server may detect this condition by the presence of a `TCN` header in a choice response before it is sent:

```http
HTTP/1.1 506 Variant Also Negotiates
Date: Mon, 22 Jul 2024 10:00:00 GMT
Server: Apache/2.4.41 (Unix)
Content-Type: text/html; charset=UTF-8
Content-Length: 233
TCN: list
Vary: negotiate,accept-language
Alternates: {"index.html.en" 1 {type text/html} {language en} {length 48}}, {"another-map.html.fr.map" 1 {type text/html} {language fr} {length 45}}}}

  506 Variant Also Negotiates

  Variant Also Negotiates
  A variant for the requested resource is itself a negotiable resource. This indicates a configuration error.

```
