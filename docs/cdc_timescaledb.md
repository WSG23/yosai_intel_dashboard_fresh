# Logical Replication Slots for TimescaleDB

Logical replication slots allow applications to consume a stream of database changes.
They are commonly used with change data capture frameworks such as Debezium.
The slot retains WAL records until they are consumed, ensuring no updates are lost.

## Creating a Slot

The following SQL creates a dedicated replication role and slot for the dashboard:

```sql
-- Create a role with replication privileges
CREATE ROLE cdc_replication WITH REPLICATION LOGIN PASSWORD 'CHANGE_ME';

-- Create a logical replication slot using the pgoutput plugin
SELECT pg_create_logical_replication_slot('cdc_slot', 'pgoutput');
```

## Debezium Connector

A Debezium connector can stream the slot to Kafka. Example configuration:

```json
{
  "name": "timescale-cdc",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.user": "cdc_replication",
    "database.password": "CHANGE_ME",
    "database.dbname": "app",
    "plugin.name": "pgoutput",
    "slot.name": "cdc_slot",
    "slot.drop.on.stop": "false",
    "publication.autocreate.mode": "filtered",
    "schema.include.list": "public"
  }
}
```

The configuration is available in `deploy/cdc/debezium-connector.json` and the SQL
in `deploy/cdc/logical_replication.sql` for production use.

## Monitoring

`monitoring/replication_lag.py` exposes a Prometheus gauge
`replication_lag_bytes` which queries `pg_replication_slots` and records
how many bytes of WAL are pending for a slot. The included Prometheus rule
raises an alert when the lag grows beyond a threshold.

Regularly check the metric and consider pruning or restarting consumers if
lag continues to increase.
