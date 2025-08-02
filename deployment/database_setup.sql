-- database_setup.sql
-- Run this SQL to create your database tables

-- Enable query statistics extension for profiling and optimization
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create facilities table
CREATE TABLE IF NOT EXISTS facilities (
    facility_id VARCHAR(50) PRIMARY KEY,
    facility_name VARCHAR(200) NOT NULL,
    campus_id VARCHAR(50),
    address TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    operating_hours JSONB,
    security_level INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create doors table
CREATE TABLE IF NOT EXISTS doors (
    door_id VARCHAR(50) PRIMARY KEY,
    door_name VARCHAR(200) NOT NULL,
    facility_id VARCHAR(50) REFERENCES facilities(facility_id),
    area_id VARCHAR(50),
    floor VARCHAR(20),
    door_type VARCHAR(20) DEFAULT 'standard',
    required_clearance INTEGER DEFAULT 1,
    is_critical BOOLEAN DEFAULT FALSE,
    location_coordinates POINT,
    device_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create people table
CREATE TABLE IF NOT EXISTS people (
    person_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200),
    employee_id VARCHAR(50),
    department VARCHAR(100),
    clearance_level INTEGER DEFAULT 1,
    access_groups TEXT[],
    is_visitor BOOLEAN DEFAULT FALSE,
    host_person_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP,
    risk_score FLOAT DEFAULT 0.0
);

-- Create access_events table (main table)
CREATE TABLE IF NOT EXISTS access_events (
    event_id VARCHAR(50) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    person_id VARCHAR(50),
    door_id VARCHAR(50) REFERENCES doors(door_id),
    badge_id VARCHAR(50),
    access_result VARCHAR(20) NOT NULL,
    badge_status VARCHAR(20),
    door_held_open_time FLOAT DEFAULT 0.0,
    entry_without_badge BOOLEAN DEFAULT FALSE,
    device_status VARCHAR(50) DEFAULT 'normal',
    raw_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create anomaly_detections table
CREATE TABLE IF NOT EXISTS anomaly_detections (
    anomaly_id VARCHAR(50) PRIMARY KEY,
    event_id VARCHAR(50) REFERENCES access_events(event_id),
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence_score FLOAT NOT NULL,
    description TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ai_model_version VARCHAR(50),
    additional_context JSONB,
    is_verified BOOLEAN,
    verified_by VARCHAR(50),
    verified_at TIMESTAMP
);

-- Create incident_tickets table
CREATE TABLE IF NOT EXISTS incident_tickets (
    ticket_id VARCHAR(50) PRIMARY KEY,
    event_id VARCHAR(50) REFERENCES access_events(event_id),
    anomaly_id VARCHAR(50) REFERENCES anomaly_detections(anomaly_id),
    status VARCHAR(30) DEFAULT 'new',
    threat_score INTEGER DEFAULT 0,
    facility_location VARCHAR(200),
    area VARCHAR(100),
    device_id VARCHAR(50),
    access_group VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_to VARCHAR(50),
    resolved_at TIMESTAMP,
    resolution_type VARCHAR(50),
    resolution_notes TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_access_events_timestamp ON access_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_access_events_person_id ON access_events(person_id);
CREATE INDEX IF NOT EXISTS idx_access_events_door_id ON access_events(door_id);
CREATE INDEX IF NOT EXISTS idx_anomaly_detections_detected_at ON anomaly_detections(detected_at);
CREATE INDEX IF NOT EXISTS idx_anomaly_detections_type ON anomaly_detections(anomaly_type);
CREATE INDEX IF NOT EXISTS idx_incident_tickets_status ON incident_tickets(status);

-- Insert sample facilities
INSERT INTO facilities (facility_id, facility_name, campus_id) VALUES 
('FAC001', 'HQ Tower - East Wing', 'CAMPUS_HQ'),
('FAC002', 'Research Lab Building', 'CAMPUS_HQ'),
('FAC003', 'Data Center Alpha', 'CAMPUS_DC')
ON CONFLICT (facility_id) DO NOTHING;

-- Insert sample doors
INSERT INTO doors (door_id, door_name, facility_id, area_id, door_type, is_critical) VALUES 
('DOOR001', 'Main Entrance', 'FAC001', 'LOBBY', 'standard', false),
('DOOR002', 'Server Room A', 'FAC001', 'SERVER', 'critical', true),
('DOOR003', 'Executive Floor', 'FAC001', 'EXEC', 'restricted', true),
('DOOR004', 'Lab Entrance', 'FAC002', 'LAB_A', 'standard', false),
('DOOR005', 'Clean Room', 'FAC002', 'LAB_B', 'critical', true)
ON CONFLICT (door_id) DO NOTHING;