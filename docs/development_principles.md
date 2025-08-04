# Development Principles

- Prefer `dataclasses` or `attrs` frozen models over mutable dictionaries and lists for internal state.
- Use functional tools like `map`, `filter`, and comprehensions when transforming collections.
- Validate immutability in tests by attempting to mutate frozen objects and ensuring exceptions are raised.
