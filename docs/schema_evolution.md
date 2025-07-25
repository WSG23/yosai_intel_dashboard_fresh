# Avro Schema Evolution

Avro schemas stored under `schemas/avro/` follow semantic
versioning. Compatibility is ensured by only applying
backward compatible changes. The following rules apply:

- Fields may be added with a default value.
- Existing fields must not be removed or change type.
- Optional fields should use a union with `null` as the first type.

Compatibility of new schemas is validated in CI using the
`scripts/check_schema_compatibility.py` tool which parses
all schema files and fails if any are invalid.

Generated reference documentation for each schema is available under
[`docs/avro/`](avro/).
