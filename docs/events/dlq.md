# Kafka Dead Letter Queue

Kafka consumers publish records that cannot be processed to a dedicated
`dead-letter` topic. Messages remain there until they are inspected and
replayed.

## Processing

Use the `scripts/kafka-replay.sh` helper to replay messages from the dead-letter
queue back to a primary topic once the underlying issue is fixed:

```bash
# Replay all messages from dead-letter to access-events
scripts/kafka-replay.sh dead-letter access-events
```

The script relies on the Kafka command line tools (`kafka-console-consumer` and
`kafka-console-producer`) being available in your `PATH`.
