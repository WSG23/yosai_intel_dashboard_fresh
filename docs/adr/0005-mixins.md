# ADR 0005: Mixins

## Context
Several classes needed shared helpers without fitting into a strict inheritance hierarchy.

## Decision
Use mixin classes to compose optional behavior, allowing classes to inherit multiple small feature sets.

## Consequences
- Promotes reuse of focused capabilities.
- Multiple inheritance can complicate method resolution if overused.
