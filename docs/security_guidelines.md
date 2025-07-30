# Security Guidelines

## Safe Database Queries

- Use parameterized queries whenever inserting values into SQL statements.
- For asyncpg, prefer `$1`, `$2`, etc. placeholders or SQLAlchemy bind parameters.
- Avoid formatting user input directly into query strings.
- Quote identifiers like table names using `asyncpg.utils._quote_ident` when dynamic.
