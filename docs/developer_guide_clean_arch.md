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
new layout. Pass `--dry-run` to preview the changes. The `--backup <dir>` option
saves copies of each directory before moving them. Use `--rollback` together
with `--backup` to restore the directories from those backups. After moving
files execute `python scripts/update_imports.py` to rewrite import statements.

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
For detecting leftover modules or unused code run:
```bash
python archive/legacy_code_detector.py
```
## Backups and Rollback

The migration script can create an archive of the directories it moves. Use `--backup` with the target path:

```bash
python scripts/migrate_to_clean_arch.py --backup /tmp/clean_arch_backup.tar.gz
```

To revert a failed migration provide the same file to `--rollback`:

```bash
python scripts/migrate_to_clean_arch.py --rollback /tmp/clean_arch_backup.tar.gz
```

### Zero-downtime tips

- Run the migration on a staging instance first using `--dry-run` and verify that the archive contains all expected directories.
- Ensure sufficient disk space is available for the backup archive.
- Apply the migration incrementally across servers: migrate one instance, restart it, confirm health checks, then proceed with the next.
- If an error occurs or the service does not start, roll back immediately using the archive and restart the node.

