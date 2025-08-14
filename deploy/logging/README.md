# Logging Deployment

This directory contains a sample Fluent Bit configuration used to forward
container logs to both Elasticsearch (for ELK) and Datadog. Deploy the Fluent
Bit sidecar alongside services like `gateway` to enable centralised log
collection.

1. Set `ELASTICSEARCH_HOST` and `DATADOG_API_KEY` environment variables.
2. Mount `fluent-bit-config.yaml` into the Fluent Bit container at
   `/fluent-bit/etc/fluent-bit.conf`.
3. Confirm in staging that logs appear in both Kibana and the Datadog Log
   Explorer using the correlation ID field.
