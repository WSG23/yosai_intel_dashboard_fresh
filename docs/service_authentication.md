# Service Authentication

Microservices communicate using signed JWT tokens. Each service signs a short
lived token with the shared `JWT_SECRET` environment variable. The token must
contain an `iss` claim identifying the calling service and an `exp` claim.

The helper module `services.security.jwt_service` raises a `RuntimeError`
if `JWT_SECRET` is not defined so the secret must always be provided.

Gateway and microservices validate the `Authorization` header on every request.
If the token is missing, expired or the `iss` claim is empty, the request is
rejected with HTTP 401.

Use the helper functions in `services.security.jwt_service` to generate and
verify these tokens when communicating between services.

## Login Sequence

![Login flow](auth_flow.png)

1. The user submits credentials to the gateway.
2. A signed JWT is created when authentication succeeds.
3. The response returns the token and a CSRF cookie.

## Token Issuance

![Token issuance](auth_flow.png)

1. Services request new tokens from the gateway using their own credentials.
2. Tokens include an issuer claim so downstream services can identify callers.

## Service-to-Service Authentication

![Service authentication](auth_flow.png)

1. Service A calls Service B with the JWT in the `Authorization` header.
2. Service B verifies the signature and expiration time.
3. Requests lacking the JWT or CSRF header are rejected with `401`.
