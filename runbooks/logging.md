# Logging Verification

This runbook outlines how to verify that application logs are collected in staging.

1. **Deploy Fluent Bit**
   - Apply the configuration in `deploy/logging/fluent-bit-config.yaml` to the staging cluster.
   - Ensure the Fluent Bit sidecar is running alongside application pods.
2. **Trigger Logs**
   - Send a request to the gateway and note the `X-Correlation-ID` header or generated ID.
3. **Check Datadog**
   - In Datadog Logs, search for `correlation_id:<ID>`.
4. **Check Elasticsearch/Kibana**
   - Query the `gateway` index for `correlation_id:"<ID>"`.
5. **Expected Result**
   - The log entry should appear in both systems within a minute of the request.
