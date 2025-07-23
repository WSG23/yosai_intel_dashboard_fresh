# Service Authentication

Microservices communicate using signed JWT tokens. Each service signs a short
lived token with the shared `JWT_SECRET` environment variable. The token must
contain an `iss` claim identifying the calling service and an `exp` claim.

Gateway and microservices validate the `Authorization` header on every request.
If the token is missing, expired or the `iss` claim is empty, the request is
rejected with HTTP 401.

Use the helper functions in `services.security.jwt_service` to generate and
verify these tokens when communicating between services.
