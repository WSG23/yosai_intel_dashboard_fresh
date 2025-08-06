# Context-Aware Analytics

The analytics pipeline can optionally incorporate environmental context
such as weather conditions, nearby events and social media sentiment.
These signals are fetched from external APIs and may be persisted in a
TimescaleDB instance for historical analysis.

## Configuration

The following environment variables control the integrations:

| Variable | Description |
|----------|-------------|
| `WEATHER_API_URL` | Weather endpoint compatible with the Open‑Meteo API. |
| `EVENTS_API_URL` | HTTP endpoint returning upcoming events for a city. |
| `SOCIAL_API_URL` | Endpoint providing social sentiment (range -1 to 1). |
| `CONTEXT_DB_DSN` | PostgreSQL/TimescaleDB DSN used by `TimescaleContextStore`. |

Unset variables disable their respective providers.

## Usage

```python
from analytics import context_providers, context_storage, risk_scoring

# gather context
ctx = context_providers.gather_context(latitude=35.0, longitude=139.0, city="Tokyo")

# persist
store = context_storage.InMemoryContextStore()
store.save(ctx.weather)

# apply to risk scoring
result = risk_scoring.calculate_risk_score(50, 20, 30, context=ctx.__dict__)
print(result)
```

The context object is a simple dataclass.  When supplied to
`calculate_risk_score` or `combine_risk_factors` it adjusts the final
score, allowing the dashboard to account for external factors.
