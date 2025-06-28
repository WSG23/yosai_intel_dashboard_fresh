# JSON Serialization Plugin Integration

This guide shows how to enable and use the built-in JSON Serialization Plugin.

## Step 1: Update `core/app_factory.py`
Add the `PluginManager` after your container creation:

```python
from core.plugins.manager import PluginManager

# Create container with YAML config (existing code)
container = get_configured_container_with_yaml(config_manager)

# NEW: Add plugin manager
plugin_manager = PluginManager(container, config_manager)

# Load all plugins
plugin_results = plugin_manager.load_all_plugins()
logger.info(f"Loaded plugins: {plugin_results}")

# Store plugin manager in app for callback registration
app._yosai_plugin_manager = plugin_manager

# Register plugin callbacks
plugin_callback_results = plugin_manager.register_plugin_callbacks(app)
logger.info(f"Registered plugin callbacks: {plugin_callback_results}")
```

## Step 2: Update `config/config.yaml`
Add the plugin configuration:

```yaml
plugins:
  json_serialization:
    enabled: true
    max_dataframe_rows: 1000
    max_string_length: 10000
    include_type_metadata: true
    compress_large_objects: true
    fallback_to_repr: true
    auto_wrap_callbacks: true
```

## Step 3: Use the plugin in callbacks
Decorate your callbacks with `safe_callback`:

```python
from core.plugins.decorators import safe_callback

@app.callback(...)
@safe_callback(app)  # Plugin handles JSON serialization
@role_required("admin")
def your_callback_function(inputs...):
    # Your existing logic
    return some_dataframe, some_function, some_complex_object
```

## Step 4: Test the plugin
Run the tests and start the app:

```bash
python -m pytest tests/test_json_serialization_plugin.py -v
python3 app.py
```

## Step 5: Monitor plugin health
Expose a health endpoint:

```python
@server.route("/health/plugins")
def plugin_health():
    if hasattr(app, '_yosai_plugin_manager'):
        health = app._yosai_plugin_manager.get_plugin_health()
        return jsonify(health)
    return jsonify({"error": "Plugin manager not available"})
```

