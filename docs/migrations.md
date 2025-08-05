# Migration Guides

This directory collects scripts and tips for upgrading the dashboard across major versions.

## Converting legacy pickle mappings

Older releases stored learned device mappings in a `learned_mappings.pkl` file. The dashboard no longer loads pickle data because unpickling arbitrary files is insecure.

Run `tools/migrate_pickle_mappings.py` to convert the file to JSON:

```bash
python tools/migrate_pickle_mappings.py /path/to/learned_mappings.pkl
```

Pass `--remove-pickle` to delete the original file after a successful conversion:

```bash
python tools/migrate_pickle_mappings.py --remove-pickle /path/to/learned_mappings.pkl
```

The JSON output is written next to the pickle using the `.json` extension. Once migrated, configure your deployment to rely only on the JSON file.

## Verifying TimescaleDB migrations

Use the `scripts/verify_timescale_migration.py` helper to confirm that a database migration completed successfully:

```bash
python scripts/verify_timescale_migration.py
```

The script checks hypertables, migrated event counts, and basic query performance. It exits with a non-zero status if the migration is incomplete.
