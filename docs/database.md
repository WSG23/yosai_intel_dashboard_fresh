# Database Schema Overview

This document summarises the relational schema used by the dashboard and records the indexing strategies applied for efficient queries.

## Entity Relationship Diagram

See [database/er_diagram.md](database/er_diagram.md) for an up-to-date diagram generated from the SQL migrations.

## Indexing Strategy

The schema defines several indexes to optimise common lookups:

- `idx_access_events_person_timestamp` on `access_events(person_id, timestamp)` accelerates person-based history queries.
- `idx_access_events_door_timestamp` on `access_events(door_id, timestamp)` improves door-centric range scans.
- `idx_access_events_person_id` and `idx_access_events_door_id` support direct filtering when only a single column is provided.
- `idx_anomaly_detections_detected_at` and `idx_anomaly_detections_type` speed up anomaly searches by time and type.
- `idx_incident_tickets_status` enables efficient ticket queue processing by status.

These indexes reduce table scans and help prevent N+1 query patterns by ensuring that frequent join and filter operations are covered.
