-- Add indexes identified from query logs
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_access_events_timestamp ON access_events(timestamp);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_anomaly_detections_detected_at ON anomaly_detections(detected_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_anomaly_detections_type ON anomaly_detections(anomaly_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_incident_tickets_status ON incident_tickets(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_doors_facility_id ON doors(facility_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_doors_is_critical ON doors(is_critical);
