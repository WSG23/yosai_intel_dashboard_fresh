# Column Verification Component

The column verification UI helps map uploaded CSV headers to standard fields.
It relies on **Dash** and **dash-bootstrap-components** for rendering and uses
`pandas` to inspect uploaded files. Optional AI suggestions come from the
`ComponentPluginAdapter` so plugins can provide smarter mappings.

## Usage

Call `register_callbacks` during application startup to enable the interactive
features. The function expects a `TrulyUnifiedCallbacks` instance:

```python
from yosai_intel_dashboard.src.components.column_verification import register_callbacks
from core.truly_unified_callbacks import TrulyUnifiedCallbacks

callbacks = TrulyUnifiedCallbacks(app)
register_callbacks(callbacks)
```

`register_callbacks` attaches `save_column_mappings_callback` so the button with
ID `save-column-mappings` writes the selected mappings using
`save_verified_mappings` and updates its label to confirm success.

## Dependencies

- `dash`
- `dash-bootstrap-components`
- `pandas`

These packages are listed in `requirements-ui.txt` and `requirements.txt`.
Ensure they are installed before enabling the component.

