# Import Dependency Map

This document outlines the high level import relationships between the main
packages.  Understanding these connections helps avoid circular imports and
clarifies where lazy loading is required.

```
start_api.py
 └─ utils
     └─ preview_utils
         └─ config
             └─ services.registry
                 └─ services.analytics.upload_analytics
                     └─ services.chunked_analysis
                        └─ validation.security_validator
                             └─ security.events.security_unified_callbacks
                                 └─ core.callback_events
```

Key points:

* Configuration no longer resolves optional services at import time.  Functions
  such as `config.service_integration.get_database_manager()` retrieve services
  from the registry when called, preventing early imports.
* The `security.events` module exposes `security_unified_callbacks` and
  `CallbackEvent` from the lightweight `core.callback_events` module. This
  removes a link in the chain that previously pulled in the entire callback
  controller during start-up.
* All modules that require callback event constants should import them from
  `core.callback_events` to keep dependencies minimal.

The new structure eliminates the circular chain between `config` and
`services` while keeping the callback system accessible.
