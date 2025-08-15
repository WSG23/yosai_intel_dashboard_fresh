-- Create a role with replication privileges
CREATE ROLE cdc_replication WITH REPLICATION LOGIN PASSWORD 'CHANGE_ME';

-- Create a logical replication slot for Debezium
SELECT pg_create_logical_replication_slot('cdc_slot', 'pgoutput');
