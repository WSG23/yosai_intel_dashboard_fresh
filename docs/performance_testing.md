# Performance Testing

This repository includes load tests using **k6** and **Gatling**. The tests
exercise the API gateway, event ingestion service and analytics endpoints under
sustained load.

## Running the Stack

Spin up the required services using the compose file in `load-tests`:

```bash
docker-compose -f load-tests/docker-compose.yml up -d
```

Kafka brokers and TimescaleDB will be available locally. Once the containers are
ready you can run the load tests.

## k6 Scenarios

The `load-tests/k6/scenarios` directory contains three scripts:

- `api-gateway-test.js` – queries the gateway health endpoint.
- `event-ingestion-test.js` – posts synthetic events at 100k events/second.
- `analytics-queries-test.js` – exercises analytics search endpoints.

Execute a scenario with:

```bash
k6 run load-tests/k6/scenarios/api-gateway-test.js
```

Results can be exported as JSON and verified against the budgets defined in
`config/performance_budgets.yml` using the `check_thresholds.sh` helper script.

## Gatling Simulations

Scala simulations live under `load-tests/gatling`. They generate sustained load
against the gateway and analytics service. Run them with the official Gatling
Docker image:

```bash
docker run --rm -v $(pwd)/load-tests/gatling:/opt/gatling/user-files \
  -v $(pwd)/load-tests/results:/opt/gatling/results gatling/gatling
```

## Grafana Dashboards

Import the dashboards in `dashboards/grafana` to visualise request rates and
latency while tests are running. The `load_testing.json` dashboard includes
panels for error rate and p95 request duration.

## Continuous Integration

The workflow `.github/workflows/performance-tests.yml` executes all scenarios on
pull requests. The job fails if the metrics in `config/performance_budgets.yml`
are exceeded.
