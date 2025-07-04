# ML Model Cards

This page summarizes the machine learning components used in the dashboard and how to interpret their outputs.

## Anomaly Detector

### Purpose
Detect unusual access events and assess security risk.

### Training Data
Uses historical access logs from the facility. No external dataset is required.

### Algorithms
Isolation Forest plus statistical and pattern‑based checks.

### Expected Inputs
`pandas.DataFrame` with at least `timestamp`, `person_id`, `door_id`, and `access_result` columns.

### Expected Outputs
Dictionary describing anomalies, severity distribution, risk assessment and recommended actions.

### Limitations
Requires roughly ten or more events to produce meaningful results and can generate false positives on very small datasets.

## Security Patterns Analyzer

### Purpose
Identify suspicious access patterns and generate a holistic security score.

### Training Data
Relies on recent access records from your own environment; no pretrained model is bundled.

### Algorithms
Isolation Forest, statistical tests and rule-based heuristics.

### Expected Inputs
DataFrame with access logs containing timestamps, user IDs, door IDs and results.

### Expected Outputs
`SecurityAssessment` dataclass (or dictionary) containing threat indicators, overall score, risk level and recommendations.

### Limitations
Requires all mandatory columns to be present. Baseline thresholds may need tuning for different deployments.

## User Behavior Analyzer

### Purpose
Cluster user activity to highlight high‑risk behavior.

### Training Data
Uses recent access history; clusters are recalculated on demand.

### Algorithms
K‑Means clustering with feature scaling.

### Expected Inputs
Access log DataFrame with at least five events per user.

### Expected Outputs
`BehaviorAnalysis` data with insights, high risk user counts and recommendations.

### Limitations
Accuracy decreases if many users have too few events. Results depend on selected cluster count.

## Unique Pattern Analyzer

### Purpose
Find unusual combinations of users, devices and times.

### Training Data
Operates on processed access logs; no separate training phase.

### Algorithms
Descriptive statistics and outlier detection using standard deviation thresholds.

### Expected Inputs
DataFrame containing timestamp, person and door identifiers along with access results.

### Expected Outputs
Dictionary summarizing user patterns, device patterns and network analysis with suggested actions.

### Limitations
Requires valid timestamps and may skip analysis if data is incomplete.

## Security Score Calculator

### Purpose
Score overall facility security using weighted event rates.

### Training Data
Statistical baselines embedded in the code; it learns from the provided event logs.

### Algorithms
Weighted z‑score calculations over failure, badge issue, after‑hours and weekend rates.

### Expected Inputs
DataFrame with `access_result`, `badge_status` and `timestamp` columns.

### Expected Outputs
Dictionary with numerical score, threat level and confidence interval.

### Limitations
Assumes enough events (around thirty) for confidence calculations and may misclassify if baseline values do not match the environment.

