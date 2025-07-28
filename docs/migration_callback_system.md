# Callback System Migration

This release finalizes the move to the unified callback framework. The
The legacy coordinator classes have been removed. Modules should now rely solely
on `TrulyUnifiedCallbacks`,
`CallbackManager` for event hooks and, when multiple steps need to be executed,
`UnifiedCallbackManager` (the alias of `TrulyUnifiedCallbacks` exported from
`core.callbacks`).

## Migrating

1. Import `TrulyUnifiedCallbacks` for registering Dash callbacks.
2. Import `CallbackManager` and `CallbackEvent` from `core` and register event
   hooks using `CallbackManager.register_callback`.
3. Trigger events via `CallbackManager.trigger` or `trigger_async`.
4. Organize multi-step operations using `UnifiedCallbackManager` imported from
   `core.callbacks` (alias of `TrulyUnifiedCallbacks`) and call `execute_group`
   within Dash callbacks.
5. `trigger_async` now executes callbacks concurrently. Use
   `UnifiedCallbackManager.execute_group_async` to run operations in parallel
   when they are IO bound.


All modules must migrate to this API before upgrading. The legacy wrappers are
no longer shipped with the project.

## Cleanup Utility Example

The repository provides `legacy_callback_migrator.py` which rewrites any
remaining references to `callback_controller` and verifies that the unified
callback system works correctly. Run it from the project root:

```bash
python legacy_callback_migrator.py --dry-run
```

Omit `--dry-run` to apply the changes. The script scans for deprecated imports,
adds the required `TrulyUnifiedCallbacks` import if missing and performs a
simple runtime validation of the new system.

## Best Practices for Migration

- **Always specify `callback_id` and `component_name`** when calling
  `TrulyUnifiedCallbacks.register_callback`. Unique identifiers allow the
  framework to detect duplicate output registrations and group callbacks by
  namespace.
- **Check for conflicts** using `callbacks.get_callback_conflicts()` before
  deploying. The registry prevents accidental duplicates but reviewing the
  report helps catch logical errors in complex pages.
- **Enable Unicode safety** with `unicode_safe=True` or by using
  `UnicodeAwareTrulyUnifiedCallbacks`. Surrogate pairs and non‑printable
  characters are sanitized automatically to avoid UTF‑8 errors.
- **Remove legacy imports** after migration and verify that tests pass. The
  `legacy_callback_migrator.py` script can assist with large refactors.
