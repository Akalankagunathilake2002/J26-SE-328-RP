# RESTful API Architecture and Design Principles

## Core Architectural Constraints
Representational State Transfer (REST) is an architectural style designed for distributed hypermedia systems. Formulated by Roy Fielding, REST relies on several foundational constraints:
1. **Client-Server Separation**: Separation of concerns allows client user interfaces and backend data storage to evolve independently.
2. **Statelessness**: Every HTTP request from client to server must contain all the information necessary to understand and complete the request. The server does not store client session context between requests.
3. **Cacheability**: Responses must define whether they are cacheable or non-cacheable to prevent clients from reusing stale data.
4. **Uniform Interface**: Resource identification via URIs, resource manipulation through representations (e.g., JSON), self-descriptive messages, and hypermedia (HATEOAS).

## HTTP Methods and Idempotence
In professional backend engineering, selecting the correct HTTP verb conveys semantic intent:
- **GET**: Retrieves a resource representation. Must be safe and idempotent (calling GET repeatedly must not cause side effects).
- **POST**: Creates a subordinate resource or executes a processing action. It is neither safe nor idempotent.
- **PUT**: Replaces the entire resource state with the supplied payload. Idempotent.
- **PATCH**: Applies a partial update to an existing resource.
- **DELETE**: Removes the specified resource. Idempotent.

## Standard HTTP Status Codes
Backend APIs must communicate outcome status unambiguously:
- `200 OK`: Request succeeded with payload.
- `201 Created`: Resource successfully created (typically includes `Location` header).
- `204 No Content`: Action succeeded without returning response body.
- `400 Bad Request`: Client validation error or malformed JSON.
- `401 Unauthorized`: Authentication credential missing or invalid.
- `403 Forbidden`: Authenticated user lacks permission for the resource.
- `404 Not Found`: Target resource URI does not exist.
- `500 Internal Server Error`: Unhandled server-side exception.
