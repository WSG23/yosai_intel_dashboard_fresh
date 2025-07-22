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
