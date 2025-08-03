# Development Principles

This project favors immutable data structures to reduce side effects and
improve reasoning about state.

- Use `dataclasses` with `frozen=True` or `attrs` frozen models instead of
  mutable dictionaries and lists for structured data.
- Prefer functional transformations such as `map`, `filter`, and
  comprehensions over manual loops.
- Validate immutability in tests by asserting that attempts to mutate frozen
  objects raise `FrozenInstanceError`.

These principles help maintain a predictable and maintainable codebase.

