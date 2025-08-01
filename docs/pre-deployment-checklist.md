# Pre-deployment Migration Checklist

Follow this checklist before rolling out a new release to ensure the database schema is up to date and consistent.

1. **Verify connectivity**
   - Confirm that `gateway_db`, `events_db` and `analytics_db` DSNs in `migrations/alembic.ini` point to the target databases.
   - Test connections using `psql` or another client.
2. **Preview the migrations**
   - Run `python scripts/migrate.py --dry-run` to output the SQL statements without executing them.
   - Review the output for unexpected changes.
3. **Review expected schema**
   - Compare the planned changes with the reference in [docs/database_schema.md](database_schema.md).
4. **Apply migrations**
   - Execute `python scripts/migrate.py` from a clean git working tree.
   - The script aborts if uncommitted changes are detected and automatically rolls back on failure.
5. **Verify results**
   - Check that all Alembic versions tables show the latest revision for each database.
   - For TimescaleDB tables, ensure hypertables exist using `\dx` and `\dt+` in `psql`.
   - Run `python -m services.index_optimizer_cli analyze` to identify any missing indexes.
6. **Backup**
   - Take a fresh database backup after successful migration as part of the release procedure.
