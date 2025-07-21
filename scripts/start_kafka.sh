#!/bin/bash
set -e

# Start the Kafka cluster defined in docker-compose.kafka.yml

echo "Starting Kafka services..."
docker-compose -f docker-compose.kafka.yml up -d
