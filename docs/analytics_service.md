# Analytics Service

The Analytics Service powers data insights in the dashboard. It processes uploads or database records, applies mappings, and generates summaries for the UI.

## Centralized Architecture

Analytics functionality is now provided through the `analytics_core` package. Create a manager using:

```python
from analytics_core import create_manager
manager = create_manager()
```

Services are accessed through the manager:

```python
dashboard = manager.core_service.get_dashboard_summary()
ai_data = manager.ai_service.process(my_data)
```

All callbacks are registered via `manager.callback_manager` and Unicode handling uses `manager.unicode_processor` utilities.

## Responsibilities

- Load uploaded files and consolidate them with existing mappings
- Clean and map columns and device identifiers
- Produce analytics such as event counts and top users/doors
- Provide sample or database-based summaries when needed

## Data Flow

1. User uploads files or selects a data source.
2. The manager routes processing to the appropriate analytics service.
3. Cleaned data is combined and analytics are computed.
4. Results are returned to the dashboard.


