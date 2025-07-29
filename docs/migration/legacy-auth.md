# Legacy Auth Migration

The legacy authentication system relied on a collection of Flask blueprints and custom session handlers. This implementation has been superseded by the unified authentication service located in `services/auth_service.py`.

## Migration Steps

1. Remove any imports of `legacy_auth` modules.
2. Update your login flows to call methods on `AuthService`.
3. Ensure tokens are issued via the new service and update configuration files accordingly.
