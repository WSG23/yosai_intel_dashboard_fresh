# Developer Guide – Clean Architecture

This guide explains how to work with the Clean Architecture layout introduced in
`yosai_intel_dashboard/`.

## Directory Overview

See [clean_architecture_structure.md](clean_architecture_structure.md) for the
complete tree. The important rules are:

1. **Core** contains domain models and use cases. It must not import from
   adapters or infrastructure.
2. **Adapters** translate external input and should only depend on the core
   layer.
3. **Infrastructure** code integrates third party frameworks and may depend on
   adapters and core.
4. **Services** compose the application into deployable units.

New modules should be added under the appropriate layer. Tests live in `tests/`
with the same hierarchy.

## Migration

Run `python scripts/migrate_to_clean_arch.py` to move existing modules into the
new layout. Pass `--dry-run` to preview the changes. After moving files execute
`python scripts/update_imports.py` to rewrite import statements.

The legacy package names still work during the transition. Thin wrapper modules
re-export the new locations so existing imports keep functioning.

## Linting

`python scripts/validate_structure.py` verifies the directory layout and is run
in CI. Developers can invoke it locally via:

```bash
python scripts/validate_structure.py
```

Add this command to your pre-commit hooks to avoid accidentally adding modules in
the wrong location.
