# SecureQueryBuilder

`SecureQueryBuilder` helps construct parameterized queries while ensuring
only allow-listed identifiers are used. The `build_select` method assembles a
`SELECT` statement and automatically generates placeholders for `WHERE`
conditions.

```python
from infrastructure.database.secure_query import SecureQueryBuilder

builder = SecureQueryBuilder(
    allowed_tables={"access_events"}, allowed_columns={"id", "time"}
)
sql, params = builder.build_select(
    "access_events", ["id"], {"time": "2024-01-01"}
)
# sql -> "SELECT id FROM access_events WHERE time=$1"
# params -> ("2024-01-01",)
```
