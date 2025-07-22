# Analytics Service Unification

The repository previously contained multiple analytics service implementations:
`services/analytics.py`, `services/enhanced_analytics.py` and
`services/working_analytics_service.py`. These variants have been consolidated
into a single `services/analytics_service.py` module.

## Key Changes

- The `AnalyticsService` API remains in `services/analytics_service.py`.
- Core sample data generation and database summaries now include logic from the
  removed services.
- Unused service modules have been removed. Import `AnalyticsService` only from
  `services.analytics_service`.

## Migration Steps

1. Update any imports referencing the removed modules to use
   `services.analytics_service`.
2. Review the new `AnalyticsService` methods if you relied on
   `working_analytics_service` or `analytics.AnalyticsService`.
3. Run your tests to ensure compatibility.

## TimescaleDB Migration Checks

Continuous integration now runs a smoke test for the TimescaleDB migration
scripts. The workflow executes:

```bash
python scripts/migrate_to_timescale.py --test-mode
python scripts/verify_timescale_migration.py
```

The build fails if verification returns a non-zero status, ensuring schema
changes do not break the migration process.
