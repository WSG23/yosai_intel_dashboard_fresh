# Role-based Access Control (RBAC)

The dashboard relies on a small permission service to check whether a
user can perform an action on a given resource. Each request supplies a
`user_id`, the target `resource` and an `action` string. The service
responds with `{ "allowed": true|false }` which is consumed by
`SecurityValidator.check_permissions()`.

## Resources and Actions

Resources identify doors, facilities or dashboard features. Typical
examples are:

- `door:101` – single door identifier
- `facility:west` – facility wide scope
- `analytics` – access to analytics pages

Actions are free form strings defined by the service. Common ones are
`open`, `view`, `edit` and `admin`.

## Scopes

Permissions may be granted globally or scoped to a facility. When the
permission service receives a check request it will consider the
resource prefix (`door:` or `facility:`) to determine the scope.

## Assigning Roles

User roles are stored in the `person_roles` table created by the initial
migration. Insert records for each user with the desired role:

```sql
INSERT INTO person_roles (person_id, role) VALUES ('alice', 'admin');
```

Roles determine the default set of permissions available to a user. The
service can also evaluate entries in `access_permissions` to allow or
deny fine‑grained access to specific doors or door groups.

## Permission Service API

The permission service exposes HTTP endpoints. Two simple examples are
shown below:

```bash
# Check if Alice may open door 101
curl "$PERMISSION_SERVICE_URL/permissions/check?user_id=alice&resource=door:101&action=open"

# Assign the admin role to Alice
curl -X POST "$PERMISSION_SERVICE_URL/roles" \
  -H 'Content-Type: application/json' \
  -d '{"user_id": "alice", "role": "admin"}'
```

The service URL defaults to `http://localhost:8081`. Override it by
setting the `PERMISSION_SERVICE_URL` environment variable.
