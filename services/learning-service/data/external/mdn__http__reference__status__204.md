<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/204 -->
# 204 No Content

The HTTP **`204 No Content`** successful response status code indicates that a request has succeeded, but the client doesn't need to navigate away from its current page.
A `204` response is cacheable by default, and an ETag header is included in such cases.

A `204 No Content` in response to these request methods has the following meaning and results:

- DELETE: The action was successful, and no further information needs to be supplied.
- PUT: The action was successful, and the ETag value contains the entity tag for the new representation of that target resource.

A `204` response can be used when implementing "save and continue editing" functionality for applications like wiki sites.
In this case, a PUT request could be used to save the page contents, and a `204 No Content` response indicates to the browser that the editor should not be replaced by other content.

Note that the response must not include any content or the Content-Length header (browsers may reject responses that include content).

## Status

```http
204 No Content
```

## Examples

### Receiving a response after deleting an image

In this example, the client sends a request to delete an image using the `DELETE` method.
The request includes an Authorization header with a token to authenticate the request:

```http
DELETE /image/123 HTTP/1.1
Host: example.com
Authorization: Bearer 1234abcd
```

After successfully deleting the image, the server responds with a `204` response with no body, indicating no further information needs to be sent to the client.

```http
HTTP/1.1 204 No Content
Date: Wed, 26 Jun 2024 12:00:00 GMT
Server: Apache/2.4.1 (Unix)
```

### Receiving a response after updating with PUT

In this example, the client sends a `PUT` request to update a user's profile information.
The request includes an Authorization header with a token to authenticate the request:

```http
PUT /users/123 HTTP/1.1
Host: example.com
Content-Type: application/json
Authorization: Bearer 1234abcd

{
  "name": "Jane Doe",
  "email": "jane@example.com"
}
```

After successfully updating the user profile, the server responds with a `204` response.
The ETag header contains the entity tag for the updated resource:

```http
HTTP/1.1 204 No Content
Date: Wed, 26 Jun 2024 12:00:00 GMT
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"
Server: Apache/2.4.1 (Unix)
```
