# Column Verification Component

The column verification UI helps map uploaded CSV headers to standard fields.
It relies on **Dash** and **dash-bootstrap-components** for rendering and uses
`pandas` to inspect uploaded files. Optional AI suggestions come from the
`ComponentPluginAdapter` so plugins can provide smarter mappings.

If the plugin service is unreachable the adapter now returns an empty mapping
and records the error via ``ErrorHandler``. UI components should detect this
case and display a placeholder instead of AI powered suggestions.

## Usage

Call `register_callbacks` during application startup to enable the interactive
features. The function expects a `TrulyUnifiedCallbacks` instance:

```python
from yosai_intel_dashboard.src.components.column_verification import register_callbacks
from yosai_intel_dashboard.src.infrastructure.callbacks import TrulyUnifiedCallbacks

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

These packages are included in the core `requirements.txt` file.
Ensure it is installed before enabling the component.

