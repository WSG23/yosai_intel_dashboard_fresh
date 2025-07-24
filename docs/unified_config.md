# Unified Configuration

The configuration schema for all services is now defined in the protobuf file
`config/yosai_config.proto`.  When building the project the file is compiled to
`yosai_config_pb2.py` together with a thin `YosaiConfig` wrapper.  Services load
YAML or JSON configuration and convert it into this protobuf representation so
that Python and Go components share the same structure.

## Regenerating the schema

After editing `yosai_config.proto` run the code generation script to rebuild the
Python modules:

```bash
scripts/generate_protos.sh
```

This command invokes `protoc` with the correct include paths and updates the
`config` package.  Commit the resulting `yosai_config_pb2.py` file so other
services can use the new fields.

## Using `YosaiConfig`

`create_config_manager()` returns an instance of `YosaiConfig` which exposes
accessors like `get_app_config()` and `get_database_config()`.  Services obtain
it from the dependency injection container and operate purely on the typed
protobuf object.

