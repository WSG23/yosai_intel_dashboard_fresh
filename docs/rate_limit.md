# Gateway Rate Limiting

The gateway enforces request quotas using Redis backed token buckets. Limits are
configured in `gateway/config/ratelimit.yaml` and enabled by default in
`config/production.yaml`.

Example configuration:

```yaml
per_ip: 60
per_user: 120
per_key: 100
global: 1000
burst: 10
```

The middleware exposes remaining quota via the following headers:

* `X-RateLimit-Limit`
* `X-RateLimit-Remaining`
* `X-RateLimit-Reset`

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
