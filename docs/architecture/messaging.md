# Messaging Architecture

The dashboard now uses Kafka for asynchronous task publication. Python services
publish tasks to Kafka topics using the lightweight `KafkaClient` which wraps
the `confluent-kafka` producer.

Some Go components (e.g. the gateway task processor) still depend on RabbitMQ.
This hybrid approach will remain while those services are refactored. The
boundary between the systems is documented below:

- **Kafka** – file processing and upload workflows within the dashboard.
- **RabbitMQ** – legacy task processor in the gateway service.

## Maintenance Plan

1. Monitor RabbitMQ usage in gateway and plan migration to Kafka when feature
   parity is available.
2. Consolidate configuration once all services use Kafka.
3. Remove RabbitMQ client code and documentation after migration is complete.
