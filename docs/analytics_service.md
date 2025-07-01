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

### `DataLoader`

- `get_processed_database()` – return combined dataframe and metadata
- `_load_consolidated_mappings()` – read saved mapping information
- `_get_uploaded_data()` – retrieve uploaded files from the UI layer
- `_apply_mappings_and_combine()` – apply mappings and merge files

### `AnalyticsService`

- `get_analytics_from_uploaded_data()` – process files directly
- `get_analytics_by_source(source)` – dispatch to uploaded, sample or database data
- `_process_uploaded_data_directly()` – internal helper for uploaded datasets
-   now streams CSV files in chunks using `pandas.read_csv` to reduce memory usage
- `summarize_dataframe(df)` – build counts and distributions from a dataframe

## Data Flow

1. User uploads files or selects a data source.
2. `DataLoader` loads mappings and cleans each file.
3. Cleaned data is combined and handed to `AnalyticsService`.
4. Analytics are computed and returned to the dashboard.

### Incremental Processing

`_process_uploaded_data_directly` no longer loads every uploaded file into
memory at once. When file paths are supplied it uses the helper
`_stream_uploaded_file` which wraps `pandas.read_csv` with a `chunksize`
parameter. The yielded chunks are passed to `_aggregate_counts` to update user
and door statistics.  The final dictionary is assembled by `_build_result`.
This incremental approach prevents excessive memory usage when processing very
large CSV uploads.
