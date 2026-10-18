<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/403 -->
# 403 Forbidden

The HTTP **`403 Forbidden`** client error response status code indicates that the server understood the request but refused to process it.
This status is similar to 401, except that for **`403 Forbidden`** responses, authenticating or re-authenticating makes no difference.
The request failure is tied to application logic, such as insufficient permissions to a resource or action.

Clients that receive a `403` response should expect that repeating the request without modification will fail with the same error.
Server owners may decide to send a 404 response instead of a 403 if acknowledging the existence of a resource to clients with insufficient privileges is not desired.

## Status

```http
403 Forbidden
```

## Examples

### Request failed due to insufficient permissions

The following example request is made to an API for user management.
The request contains an Authorization header using `Bearer` authentication scheme containing an access token:

```http
DELETE /users/123 HTTP/1.1
Host: example.com
Authorization: Bearer abcd123
```

The server has authenticated the request, but the action fails due to insufficient rights and the response body contains a reason for the failure:

```http
HTTP/1.1 403 Forbidden
Date: Tue, 02 Jul 2024 12:56:49 GMT
Content-Type: application/json
Content-Length: 88

{
  "error": "InsufficientPermissions",
  "message": "Deleting users requires the 'admin' role."
}
```
