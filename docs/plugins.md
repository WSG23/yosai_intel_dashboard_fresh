# Plugins

This document explains how plugins are discovered, configured, and managed at runtime.

## Discovery

Plugins live in the `plugins/` directory by default. The `PluginManager` scans this package with `pkgutil.iter_modules` and imports every submodule. A plugin module should expose a `create_plugin()` function, a `plugin` instance, or an `init_plugin(container, config)` function that returns an object implementing `PluginProtocol`.

You can change the search location by passing a different package name to `PluginManager(package="myplugins")` when constructing it.

## Configuration

Application settings reference `core/plugins/config/plugins.yaml` for all plugin
configuration. Add the following line to your main config to include it. This
dedicated file centralizes every plugin's settings.

```yaml
plugins: !include ../../core/plugins/config/plugins.yaml
```

## Hello World Example

A very small plugin can simply register a Dash callback. The module must expose
a `create_plugin()` function so the `PluginManager` can instantiate it.

```python
# plugins/hello_world.py
from dash import Input, Output
from services.data_processing.core.protocols import CallbackPluginProtocol, PluginMetadata


class HelloWorldPlugin(CallbackPluginProtocol):
    metadata = PluginMetadata(
        name="hello_world",
        version="1.0.0",
        description="Example plugin",
        author="Example",
    )

    def register_callbacks(self, manager, container):
        @manager.app.callback(Output("hello-output", "children"), Input("hello-btn", "n_clicks"))
        def _say_hello(_):
            return "Hello World!"
        return True


def create_plugin() -> HelloWorldPlugin:
    return HelloWorldPlugin()
```

Enable the plugin in `core/plugins/config/plugins.yaml`:

```yaml
hello_world:
  enabled: true
```

## Lifecycle

For each enabled plugin the manager calls these methods:

1. `load(container, config)` – register services with the DI container.
2. `configure(config)` – apply configuration values.
3. `start()` – perform any runtime initialization.

Initialize plugins using `setup_plugins(app)` from `core.plugins.auto_config`.
This loads every enabled plugin, registers callbacks, exposes `/health/plugins`
and attaches the plugin manager as `app._yosai_plugin_manager`.

For a visual overview of discovery, dependency resolution and the lifecycle calls see [plugin_lifecycle.md](plugin_lifecycle.md).

## Dependency management

Plugins can declare dependencies on other plugins via `metadata.dependencies`. The
`PluginDependencyResolver` checks these dependencies while loading plugins. If a
circular dependency is detected the manager logs an error like:

```
Plugin dependency cycle detected: a -> b -> a
```

and no plugins will be loaded. Avoid cycles by restructuring your plugin
dependencies so they form a directed acyclic graph.
