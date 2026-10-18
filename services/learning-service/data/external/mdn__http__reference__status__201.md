<!-- role: Backend Developer / Full-Stack Developer -->
<!-- topic: HTTP Status Codes -->
<!-- source: MDN Web Docs (Mozilla Contributors) -->
<!-- license: CC BY-SA 2.5 -->
<!-- url: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/201 -->
# 201 Created

The HTTP **`201 Created`** successful response status code indicates that the HTTP request has led to the creation of a resource.
This status code is commonly sent as the result of a POST request.

The new resource, or a description and link to the new resource, is created before the response is returned.
The newly-created items can be returned in the body of the response message, but must be locatable by the **URL of the initiating request** or by the URL in the value of the Location header provided with the response.

## Status

```http
201 Created
```

## Examples

### Receiving a response indicating user creation

Let's assume there's a REST API for managing users with an endpoint at `http://example.com/users`. In this example, we send a `POST` request with the following body to create a user:

```http
POST /users HTTP/1.1
Host: example.com
Content-Type: application/json

{
  "firstName": "Brian",
  "lastName": "Smith",
  "email": "brian.smith@example.com"
}
```

After successful user creation, the `201 Created` response will look like this:

```http
HTTP/1.1 201 Created
Content-Type: application/json
Location: http://example.com/users/123

{
  "message": "New user created",
  "user": {
    "id": 123,
    "firstName": "Brian",
    "lastName": "Smith",
    "email": "brian.smith@example.com"
  }
}
```
