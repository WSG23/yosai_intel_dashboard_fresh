# Centralized Analytics Manager

The analytics system is now orchestrated by `CentralizedAnalyticsManager` from
`analytics.core`.  It coordinates the core, AI, performance and data-processing
services while exposing a single entry point for triggering analytics flows.

## Example Usage

```python
from analytics.core import create_manager

# Build a manager with the default stub services
manager = create_manager()

manager.run_full_pipeline(raw_data)
```

`run_full_pipeline` will hand off the provided data to each service in turn and
finally emit a `pipeline_complete` event using
`TrulyUnifiedCallbacks`.

## Removing Legacy Details

Previous documentation describing individual service classes has been removed.
The new manager abstracts these details, allowing implementations to evolve
independently of the calling code.

