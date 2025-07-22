# Kafka Lag Resolution Runbook

This runbook outlines steps to resolve consumer lag in Kafka topics.

## Overview
Lag typically indicates that consumers cannot keep up with the incoming message rate.

## Fetching Logs
Gather broker and consumer logs for the affected topic:

```bash
kubectl logs deployment/kafka-broker > /tmp/kafka-broker.log
kubectl logs deployment/kafka-consumer > /tmp/kafka-consumer.log
```

Attach these files to the incident ticket.

## Contacting On-Call Engineers
Notify the on-call engineer through Slack `#ops-oncall` or phone `+1-555-0100` if lag exceeds operational thresholds.

## Resolution Steps
1. Inspect consumer metrics in Grafana to determine if the lag is increasing.
2. If consumers are stalled, restart the consumer pods:
   ```bash
   kubectl rollout restart deployment/kafka-consumer
   ```
3. Monitor the lag using `kafka-consumer-groups.sh` until it returns to normal levels.
4. If the backlog persists, scale out the consumer deployment:
   ```bash
   kubectl scale deployment/kafka-consumer --replicas=2
   ```
5. Escalate to the on-call engineer if no improvement is observed.
