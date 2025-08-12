# Parameterized time intervals

To avoid SQL injection, construct dynamic time ranges using PostgreSQL's
`make_interval` with parameter placeholders rather than string concatenation.

```python
rows = await pool.fetch(
    """
    SELECT ...
    WHERE time > NOW() - make_interval(days => $1)
    """,
    days,
)
```

This pattern ensures the `days` value is treated as an integer parameter
rather than raw SQL.
