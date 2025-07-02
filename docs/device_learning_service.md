# Device Learning Service

This service manages persistent device mappings learned from uploaded files.
It stores mapping data on disk and can apply the mappings automatically
when similar files are uploaded again.

## Responsibilities

- Create fingerprints for uploaded data to uniquely identify a file format
- Persist learned device mapping information as JSON
- Reload mappings on startup and expose them to other services
- Allow user-confirmed mappings to be saved for future use

## Major Methods

- `_get_file_fingerprint(df, filename)` – build a stable identifier
- `_load_all_learned_mappings()` – initialize in-memory cache from disk
- `save_device_mappings(df, filename, device_mappings)` – store mappings
- `get_learned_mappings(df, filename)` – fetch mappings by fingerprint
- `apply_learned_mappings_to_global_store(df, filename)` – update the
  global mapping store used by the UI components
 - `save_user_device_mappings(df, filename, user_mappings)` – persist manual
   corrections provided by users using a unified file fingerprint

## Data Flow

1. A user uploads a file and confirms device mappings.
2. The service generates a fingerprint and saves mappings to
   `data/device_learning/`.
3. When a matching file is processed later, mappings are loaded and
   applied automatically.

### Legacy pickle file

Earlier versions of the dashboard stored learned mappings in
`data/learned_mappings.pkl`. Loading this pickle file has been
completely removed for security reasons. The service now persists and
loads mappings only from `data/learned_mappings.json`.
