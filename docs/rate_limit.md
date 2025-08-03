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
