# Unified Configuration

The configuration schema for all services is now defined in the protobuf file
`protobuf/config/schema/config.proto`.  When building the project the file is compiled to
`config/generated/protobuf/config/schema/config_pb2.py` together with a thin `YosaiConfig` wrapper.  Services load
YAML or JSON configuration and convert it into this protobuf representation so
that Python and Go components share the same structure.

## Regenerating the schema

After editing `protobuf/config/schema/config.proto` run the `make` target to rebuild the
Python and Go modules:

```bash
make generate-config-proto
```

This command invokes `protoc` with the correct include paths and updates the
`config/generated` packages.  Commit the resulting files so other
services can use the new fields.

## Using `YosaiConfig`

`create_config_manager()` returns an instance of `YosaiConfig` which exposes
accessors like `get_app_config()` and `get_database_config()`.  Services obtain
it from the dependency injection container and operate purely on the typed
protobuf object.

When loading configuration directly via `UnifiedLoader` the loader applies
`EnvironmentProcessor` automatically. Any environment variables prefixed with
`YOSAI_` will override the corresponding fields in the resulting protobuf
message. This mirrors the behaviour of the traditional dataclass configuration
pipeline.

