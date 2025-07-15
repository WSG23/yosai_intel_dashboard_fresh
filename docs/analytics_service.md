# Centralized Analytics Manager

The analytics system is now orchestrated by `CentralizedAnalyticsManager` from
`analytics_core`.  It coordinates the core, AI, performance and data-processing
services while exposing a single entry point for triggering analytics flows.

## Example Usage

```python
from analytics_core.centralized_analytics_manager import CentralizedAnalyticsManager
from analytics_core.services.core_service import CoreAnalyticsService
from analytics_core.services.ai_service import AIAnalyticsService
from analytics_core.services.performance_service import PerformanceAnalyticsService
from analytics_core.services.data_processing_service import DataProcessingService

manager = CentralizedAnalyticsManager(
    core_service=CoreAnalyticsService(),
    ai_service=AIAnalyticsService(),
    performance_service=PerformanceAnalyticsService(),
    data_service=DataProcessingService(),
)

manager.run_full_pipeline(raw_data)
```

`run_full_pipeline` will hand off the provided data to each service in turn and
finally emit a `pipeline_complete` event using
`UnifiedCallbackManager`.

## Removing Legacy Details

Previous documentation describing individual service classes has been removed.
The new manager abstracts these details, allowing implementations to evolve
independently of the calling code.
