# Database Schema

This reference summarises the main tables used by the dashboard. Full DDL files can be found under `deployment/` and `migrations/`.

## access_events

Stores every access control event from the facility devices. The table is configured as a hypertable when TimescaleDB is enabled.

```sql
CREATE TABLE IF NOT EXISTS access_events (
    event_id VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    person_id VARCHAR(50),
    door_id VARCHAR(50) REFERENCES doors(door_id),
    access_result VARCHAR(20) NOT NULL
    -- additional columns omitted
);
```

## anomaly_detections

Links AI-detected anomalies to the originating event.

```sql
CREATE TABLE IF NOT EXISTS anomaly_detections (
    anomaly_id VARCHAR(50) PRIMARY KEY,
    event_id VARCHAR(50) REFERENCES access_events(event_id),
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## incident_tickets

Tracks incident tickets that require human follow-up.

```sql
CREATE TABLE IF NOT EXISTS incident_tickets (
    ticket_id VARCHAR(50) PRIMARY KEY,
    event_id VARCHAR(50) REFERENCES access_events(event_id),
    status VARCHAR(30) DEFAULT 'new',
    threat_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## behavior_baselines

Used by analytics modules to persist typical behaviour metrics for people, doors and facilities.

```sql
CREATE TABLE IF NOT EXISTS behavior_baselines (
    entity_type VARCHAR(10) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    metric VARCHAR(50) NOT NULL,
    value FLOAT NOT NULL,
    PRIMARY KEY (entity_type, entity_id, metric)
);
```

## RBAC tables

Role-based access control relies on four tables to map roles and permissions to users.

```sql
CREATE TABLE IF NOT EXISTS roles (...);
CREATE TABLE IF NOT EXISTS permissions (...);
CREATE TABLE IF NOT EXISTS role_permissions (...);
CREATE TABLE IF NOT EXISTS user_roles (...);
```

## Index Optimizer

`database.index_optimizer.IndexOptimizer` inspects existing indexes and can suggest new ones. Use the CLI helper to analyse usage or create recommendations:

```bash
python -m services.index_optimizer_cli analyze
python -m services.index_optimizer_cli create <table> <column> [column...]
```

The `analyze_index_usage()` method returns current statistics while `recommend_new_indexes()` emits `CREATE INDEX` statements if columns are not indexed.

