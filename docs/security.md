# Secure Database Queries

To reduce the risk of SQL injection vulnerabilities:

- Always use parameterized queries with placeholders like `%s` or `?` rather than
  formatting values into query strings.
- Prefer the `execute_query` and `execute_command` helpers which enforce
  parameter validation.
- Never concatenate untrusted input with SQL keywords or table names.
- Validate user-supplied data types before executing a query.

Following these practices ensures that user input is passed separately from the
SQL statement, preventing malicious injections.
