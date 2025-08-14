# Gateway Rate Limiting

The gateway enforces request quotas using Redis backed token buckets. Limits are
configured in `gateway/config/ratelimit.yaml` and enabled by default in
`config/environments/production.yaml`. Application code now uses the unified
`RateLimiter` implementation in `core/security.py`; the older
`core/rate_limiter.py` module has been deprecated.

Example configuration:

```yaml
per_ip: 60
per_user: 120
per_key: 100
global: 1000
burst: 10
```

The middleware and decorators expose quota information on every response using
standard headers:

* `X-RateLimit-Limit` – maximum requests allowed per window
* `X-RateLimit-Remaining` – requests left in the current window
* `X-RateLimit-Reset` – UNIX timestamp when the window resets

When a client exceeds its quota the response will use HTTP 429 and include a
`Retry-After` header indicating the number of seconds until more requests are
permitted.

Rate limit metrics are exported alongside existing gateway metrics and can be
visualized using the default Prometheus dashboard.

## Application Tier Limits

The dynamic configuration layer supports per-tier API limits with optional
burst capacity:

```yaml
security:
  rate_limits:
    free:
      requests: 100
      window_minutes: 1
    pro:
      requests: 1000
      window_minutes: 1
      burst: 200
```

Each tier can be overridden at runtime using environment variables:

```bash
export RATE_LIMIT_PRO_REQUESTS=1500
export RATE_LIMIT_PRO_BURST=300
```

The helper `get_rate_limit(tier)` returns the final `limit`, `window`, and
`burst` values after all overrides.
