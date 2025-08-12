# Developer Security Guidelines

These guidelines outline practices for writing secure code and reviewing contributions.

## Secure Coding Patterns

- **Parameterized queries** – Always use prepared or parameterized statements when interacting with databases to prevent SQL injection.
- **Input validation and output encoding** – Validate and sanitize all external input. Encode output sent to browsers or other downstream systems.
- **Robust error handling** – Catch and handle exceptions, logging only necessary details while avoiding leakage of secrets or stack traces to users.

## Common Pitfalls

- Building SQL statements by concatenating user input.
- Trusting client-side validation without server-side checks.
- Logging or returning detailed error messages containing sensitive information.
- Committing secrets or credentials to source control.
- Using dependencies with known vulnerabilities.

## Required Security Tests

- Static analysis tools and linters for security issues.
- Dependency vulnerability scans (e.g., `pip-audit`, `npm audit`). The
  project's `dependency_checker` runs `pip-audit` after verifying pinned
  requirements and fails when high or critical vulnerabilities are detected.
- Unit tests covering authentication, authorization, and validation logic.
- Dynamic tests such as fuzzing or API security tests where applicable.

## Code Review Checklist

- [ ] All database access uses parameterized queries or safe ORM constructs.
- [ ] Input validation and output encoding are in place.
- [ ] Errors are handled gracefully without exposing sensitive details.
- [ ] Secrets and configuration values are loaded from secure storage, not committed.
- [ ] Dependencies are up to date and pass vulnerability scans.
- [ ] Security-related tests are present and passing.
- [ ] Documentation and threat models updated where necessary.

