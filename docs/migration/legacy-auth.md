# Legacy Auth Migration

The legacy authentication system relied on a collection of Flask blueprints and custom session handlers. This implementation has been superseded by the unified authentication service located in `services/auth_service.py`.

## Legacy Usage

```python
from legacy_auth import login_user

token = login_user("alice", "p@ssw0rd")
```

## New Usage

```python
from services.auth_service import AuthService

auth = AuthService()
token = auth.login("alice", "p@ssw0rd")
```

## Caveats

- Tokens issued by `AuthService` are JWTs and require synchronized clocks.
- Set the `AUTH_SERVICE_URL` environment variable before calling the service.
- Session cookies used by the legacy system are no longer supported.

## Migration Steps

1. Remove any imports of `legacy_auth` modules.
2. Update your login flows to call methods on `AuthService`.
3. Ensure tokens are issued via the new service and update configuration files accordingly.

See the [Deprecation Timeline](../deprecation_timeline.md) for important dates.
