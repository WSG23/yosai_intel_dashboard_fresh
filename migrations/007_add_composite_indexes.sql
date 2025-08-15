-- Composite indexes to optimize range queries by person and door
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_access_events_person_timestamp
    ON access_events(person_id, timestamp);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_access_events_door_timestamp
    ON access_events(door_id, timestamp);
