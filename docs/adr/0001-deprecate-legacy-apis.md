# ADR 0001: Deprecate Legacy API Shims

## Status
Accepted

## Context
Several modules and helpers were relocated as part of ongoing refactors.
Older entry points remained but gave no explicit indication that they would
be removed.

## Decision
Legacy names now wrap the new implementations and emit
`DeprecationWarning` when invoked. These shims maintain backward
compatibility while guiding consumers toward the updated modules.

## Consequences
- Users receive runtime warnings directing them to the new APIs.
- Shims can be safely removed in a future major release once consumers
  have migrated.

