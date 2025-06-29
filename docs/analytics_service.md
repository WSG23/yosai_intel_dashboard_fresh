# Analytics Service

The Analytics Service powers most data insights in the dashboard.
It processes raw uploads or database records, applies learned mappings,
and generates summaries for the UI.

## Responsibilities

- Load uploaded files and consolidate them with existing mappings
- Clean and map columns and device identifiers
- Produce analytics such as event counts and top users/doors
- Provide sample or database based summaries when needed

## Major Classes and Methods

### `AnalyticsDataAccessor`

- `get_processed_database()` – return combined dataframe and metadata
- `_load_consolidated_mappings()` – read saved mapping information
- `_get_uploaded_data()` – retrieve uploaded files from the UI layer
- `_apply_mappings_and_combine()` – apply mappings and merge files

### `AnalyticsService`

- `get_analytics_from_uploaded_data()` – process files directly
- `get_analytics_by_source(source)` – dispatch to uploaded, sample or database data
- `_process_uploaded_data_directly()` – internal helper for uploaded datasets
- `summarize_dataframe(df)` – build counts and distributions from a dataframe

## Data Flow

1. User uploads files or selects a data source.
2. `AnalyticsDataAccessor` loads mappings and cleans each file.
3. Cleaned data is combined and handed to `AnalyticsService`.
4. Analytics are computed and returned to the dashboard.
