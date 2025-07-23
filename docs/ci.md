# Continuous Integration

This repository relies on GitHub Actions workflows to run tests and safety checks for every pull request.

## Migration Check

The `migration-check.yml` workflow installs the Python dependencies and validates the Alembic migrations in dry-run mode. After the standard migration step it now also runs the Timescale migration scripts:

```bash
python scripts/migrate.py --config migrations/timescale/alembic.ini --dry-run
```

Both commands must succeed for the job to pass, ensuring the core and Timescale schemas remain in sync.
