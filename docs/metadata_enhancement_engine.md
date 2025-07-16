# Metadata Enhancement Engine

`MetadataEnhancementEngine` combines multiple analysis components to
produce enriched metadata from uploaded access records. It is registered
with the dependency injection container so other services can retrieve it
using the key `"metadata_engine"`.

## Public API

### `enhance_metadata() -> Dict[str, Any]`

Runs behavioral analysis, security refinement, pattern learning, temporal
analytics and compliance checks against the uploaded data returned by
`UploadDataService`. The result dictionary contains:

- `behavior`: counts of unique users and doors
- `security`: overall denied access rate
- `patterns`: most common user/door paths
- `temporal`: first and last event timestamps
- `compliance`: whether required columns are present
- `analytics`: dashboard summary from the analytics service

Each input dataframe should provide `person_id`, `door_id`, `timestamp`
and `access_result` columns as produced by the upload workflow.
