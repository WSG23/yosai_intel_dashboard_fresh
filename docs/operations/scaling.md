# Scaling Guidelines

This document describes resource requests, limits, and scaling thresholds for key services.

## Analytics Service
- **Resource Requests:** `200m` CPU, `256Mi` memory
- **Limits:** `1` CPU, `512Mi` memory
- **Scaling Thresholds:**
  - CPU utilization > 70%
  - Memory utilization > 75%
  - Kafka consumer lag > 100 messages per pod

## API Gateway
- **Resource Requests:** `300m` CPU, `512Mi` memory
- **Limits:** `2` CPU, `1Gi` memory
- **Scaling Thresholds:**
  - CPU utilization > 65%
  - Memory utilization > 70%
  - Kafka consumer lag > 100 messages per pod

## Event Ingestion
- **Resource Requests:** `250m` CPU, `256Mi` memory
- **Limits:** `1` CPU, `512Mi` memory
- **Scaling Thresholds:**
  - CPU utilization > 70%
  - Memory utilization > 75%
  - Kafka consumer lag > 200 messages per pod

These values are used by the HorizontalPodAutoscaler manifests in `deploy/k8s`.
