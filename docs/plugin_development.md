# Plugin Development Guide

This guide explains how to create your own plugins for the Yōsai Intel Dashboard.
Plugins extend the dashboard by registering services and Dash callbacks through
the `PluginManager`.

## Basic Structure

Each plugin lives in its own module inside the `plugins/` directory. A minimal
plugin exposes a `create_plugin()` factory that returns an object implementing
`PluginProtocol`.

```python
# plugins/my_plugin.py
from core.plugins.protocols import PluginProtocol, CallbackPluginProtocol, PluginMetadata

class MyPlugin(CallbackPluginProtocol):
    metadata = PluginMetadata(
        name="my_plugin",
        version="1.0.0",
        description="Example plugin",
        author="You",
    )

    def __init__(self) -> None:
        self.started = False

    def load(self, container, config):
        # Register services here
        return True

    def configure(self, config):
        # Apply configuration values
        return True

    def start(self):
        self.started = True
        return True

    def stop(self):
        self.started = False
        return True

    def health_check(self):
        return {"healthy": self.started}

    def register_callbacks(self, manager, container):
        # Register Dash callbacks
        return True


def create_plugin() -> MyPlugin:
    return MyPlugin()
```

### Callback Registration

Plugins that define `register_callbacks()` should implement
`CallbackPluginProtocol`. After loading all plugins call
`register_plugin_callbacks(app)` from the `PluginManager` so each plugin can
hook into Dash.

### Health Checks

Every plugin must implement `health_check()` which returns a dictionary
indicating its status. The `/health/plugins` endpoint exposes this data so you
can monitor all running plugins.

## Configuration

Plugins are enabled and configured through `config/config.yaml` under the top
level `plugins:` key. Each section is named after the plugin's metadata name.

```yaml
plugins:
  my_plugin:
    enabled: true
    option_a: 123
    option_b: "value"
```

The provided configuration dictionary is passed to `configure()` during plugin
initialisation. Disabling a plugin is as simple as setting `enabled: false`.

