# Callback System Migration

This release finalizes the move to the unified callback framework. The
The legacy coordinator classes have been removed. Modules should now rely solely
on `TrulyUnifiedCallbacks` for all callback registration and execution. Event
hooks can still be triggered via `CallbackManager` but all multi-step
operations should directly use ``TrulyUnifiedCallbacks``.

## Migrating

1. Import `TrulyUnifiedCallbacks` for registering Dash callbacks.
2. Import `CallbackManager` and `CallbackEvent` from `core` and register event
   hooks using `CallbackManager.register_callback`.
3. Trigger events via `CallbackManager.trigger` or `trigger_async`.
4. Organize multi-step operations using `TrulyUnifiedCallbacks.execute_group`
   within Dash callbacks.
5. `trigger_async` now executes callbacks concurrently. Use
   `TrulyUnifiedCallbacks.execute_group_async` to run operations in parallel when
   they are IO bound.


All modules must migrate to this API before upgrading. The legacy wrappers are
no longer shipped with the project.

## Cleaning Up Old Imports

The deprecated `core.callback_controller` module has been removed.
Search the codebase for `callback_controller` and update any remaining
references to use the unified API. Make sure to import `TrulyUnifiedCallbacks`
where required and remove any deprecated wrappers. Running the tests after
each change helps ensure the callbacks behave as expected.

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
- **Remove legacy imports** after migration and verify that tests pass. Use a
  search-and-replace workflow to update modules in bulk when refactoring.
