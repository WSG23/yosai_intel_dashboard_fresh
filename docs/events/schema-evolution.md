# Event Schema Versioning

Event schemas under `schemas/avro/` follow semantic versioning. Each schema file
name includes a suffix like `_v1.avsc` that denotes the major version. When a
schema changes, create a new file with an incremented version and keep the
previous files intact.

Existing schema files **must not** be modified in place. Instead:

- Copy the latest version to a new file with the next version number.
- Apply schema changes to that new file only.
- Register the new version with the schema registry.
- Update producers and consumers to handle the new version.

Developers can use `tools/schema_registry_client.py` to register and
inspect schemas without pulling in the full Confluent tooling. For
example, to register `schemas/avro/access_event_v1.avsc` under the
`access-events-value` subject:

```bash
python tools/schema_registry_client.py http://localhost:8081 \
  register access-events-value schemas/avro/access_event_v1.avsc
```

The `scripts/check_schema_versions.py` helper runs in CI and fails if any schema
is modified without adding a new versioned file.
