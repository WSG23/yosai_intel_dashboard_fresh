# Plugins

This document explains how plugins are discovered, configured, and managed at runtime.

## Discovery

Plugins live in the `plugins/` directory by default. The `PluginManager` scans this package with `pkgutil.iter_modules` and imports every submodule. A plugin module should expose a `create_plugin()` function, a `plugin` instance, or an `init_plugin(container, config)` function that returns an object implementing `PluginProtocol`.

You can change the search location by passing a different package name to `PluginManager(package="myplugins")` when constructing it.

## Configuration

Application settings include a top level `plugins:` section in `config/config.yaml`. Each plugin has its own subsection named after its metadata name. Set `enabled: true` to load a plugin and supply any plugin specific options under that key. These options are provided to `configure()` after the plugin is loaded.

```yaml
plugins:
  json_serialization:
    enabled: true
    max_dataframe_rows: 1000
```

## Lifecycle

For each enabled plugin the manager calls these methods:

1. `load(container, config)` – register services with the DI container.
2. `configure(config)` – apply configuration values.
3. `start()` – perform any runtime initialization.

After all plugins are loaded call `register_plugin_callbacks(app)` so callback plugins can hook into Dash. Plugins implement `health_check()` and `stop()`. The manager periodically gathers health data and exposes it via `/health/plugins`.
