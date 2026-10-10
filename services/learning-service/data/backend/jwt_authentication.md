# JSON Web Token (JWT) Authentication in Modern Backend APIs

## Overview and Core Concept
JSON Web Tokens (JWT) are an open, industry-standard (RFC 7519) method for representing claims securely between two parties. In modern stateless backend architectures (such as microservices or decoupled frontend-backend web apps), JWTs are commonly used for authorization and authentication.

Once a user logs in with their credentials (e.g., username/email and password), the backend verifies the credentials and returns a signed JWT. In subsequent requests, the client transmits this token (typically in the HTTP `Authorization` request header using the `Bearer <token>` scheme).

## Structure of a JWT
A JSON Web Token consists of three parts separated by dots (`.`):
1. **Header**: Specifies the token type (`JWT`) and the cryptographic signing algorithm (such as `HS256` or `RS256`).
2. **Payload**: Contains the claims. Claims are statements about an entity (typically the authenticated user) and additional metadata such as token expiration (`exp`), subject (`sub`), and issued-at timestamp (`iat`).
3. **Signature**: Created by taking the encoded header, the encoded payload, a secret key (or private key in asymmetric signing), and signing them using the specified algorithm.

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Ikpv...
[   Header   ] . [   Payload   ] . [   Signature   ]
```

## How Verification Works
Because the signature is computed over both the header and payload, any alteration to the payload by a third party invalidates the signature. When receiving a token, the backend recomputes the signature using its private secret. If the computed signature matches the token's signature and the expiration timestamp has not elapsed, the request is trusted without needing to perform a database session lookup.

## Industry Best Practices & Security
- **Short-Lived Access Tokens**: Keep access token lifespans short (e.g., 15 minutes) to minimize damage if a token is intercepted.
- **Refresh Token Rotation**: Pair the access token with a securely stored HTTP-only refresh token used to request new access tokens.
- **Never Store Sensitive Secrets in the Payload**: JWT payloads are Base64Url-encoded, not encrypted. Anyone can decode and inspect the payload. Sensitive information like passwords, API keys, or private PII must never be placed inside claims.
- **HTTPS Only**: Always transmit tokens over encrypted TLS connections to prevent eavesdropping and Man-in-the-Middle (MitM) attacks.
