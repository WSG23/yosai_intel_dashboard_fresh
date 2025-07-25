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
from dataclasses import dataclass
from yosai_intel_dashboard.src.services.data_processing.core.protocols import (
    PluginProtocol,
    CallbackPluginProtocol,
    PluginMetadata,
)


@dataclass
class MyPluginConfig:
    greeting: str = "hello"


class MyPlugin(CallbackPluginProtocol):
    metadata = PluginMetadata(
        name="my_plugin",
        version="1.0.0",
        description="Example plugin",
        author="You",
    )

    def __init__(self, config: MyPluginConfig) -> None:
        self.config = config
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
`CallbackPluginProtocol`. Load plugins through `setup_plugins(app)` from
`core.plugins.auto_config` so each plugin can hook into Dash automatically.
The helper exposes `/health/plugins` and attaches the plugin manager as
`app._yosai_plugin_manager`.

### Health Checks

Every plugin must implement `health_check()` which returns a dictionary
indicating its status. The `/health/plugins` endpoint exposes this data so you
can monitor all running plugins.

## Configuration

Plugins are enabled and configured through `core/plugins/config/plugins.yaml`.
This dedicated file centralizes all plugin settings. Reference it in your main
configuration:

```yaml
plugins: !include ../../core/plugins/config/plugins.yaml
```

Inside `core/plugins/config/plugins.yaml` define each plugin section:

```yaml
my_plugin:
  enabled: true
  option_a: 123
  option_b: "value"
```

The provided configuration dictionary is passed to `configure()` during plugin
initialisation. Disabling a plugin is as simple as setting `enabled: false`.

