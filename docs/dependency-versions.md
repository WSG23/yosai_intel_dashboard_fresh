# Dependency Version Pins

The following key dependencies are pinned to known-compatible versions to avoid resolver conflicts:

| Package | Version |
|---------|---------|
| Flask | 3.1.1 |
| flasgger | 0.9.7.1 |
| pandas | 2.2.3 |
| psycopg2-binary | 2.9.10 |
| uvicorn | 0.34.0 |

Ensure these versions are kept in sync across `requirements.txt` and development tooling to prevent installation issues.
