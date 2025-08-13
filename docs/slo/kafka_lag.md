# Kafka Lag SLO

- **Objective:** Consumer lag below 1,000 messages.
- **Measurement:** `kafka_consumergroup_lag`
- **Alert:** Trigger if lag exceeds 1,000 for 10 minutes.

