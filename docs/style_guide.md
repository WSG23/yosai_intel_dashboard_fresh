# Code Style Guide

This project follows the [Black](https://github.com/psf/black) code formatter with its default maximum line length of **88 characters**. The same limit is enforced by [Flake8](https://flake8.pycqa.org) and [isort](https://pycqa.github.io/isort/) through `profile = "black"`.

All checks run automatically via [pre-commit](https://pre-commit.com/) and in CI:

```bash
pre-commit run --all-files
```

### Refactoring long lines

When a line grows beyond 88 characters, split it into logical parts. Below is an example before and after applying the rule.

#### Before
```python
query = session.query(User).filter(User.created_at >= start_date, User.is_active == True).order_by(User.id.desc()).limit(1000)
```

#### After
```python
query = (
    session.query(User)
    .filter(User.created_at >= start_date, User.is_active is True)
    .order_by(User.id.desc())
    .limit(1000)
)
```

Use implicit line continuation inside parentheses and place dotted calls on separate lines. This improves readability while keeping within the 88‑character limit.
