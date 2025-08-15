# Upgrading Dependent Services

When the dashboard introduces breaking changes to event schemas or
service databases, downstream services may require updates. Follow these
steps to keep dependents compatible:

1. Review the changelog for new schema versions and database migrations.
2. Update any generated client code or ORM models that rely on the
   changed schema.
3. If consuming events, fetch the latest schema from the registry using
   `tools/schema_registry_client.py` and adjust deserializers
   accordingly.
4. Run the service's Alembic migrations to upgrade its database schema
   before deploying new code.
5. Perform end-to-end tests in a staging environment to validate the
   upgrade.

Adhering to this guide helps ensure upgrades remain coordinated across
services and prevents runtime incompatibilities.
