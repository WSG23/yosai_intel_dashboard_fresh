# MockDatabase

`MockDatabase` provides a lightweight stand-in for a real database
connection.  It implements the complete `ConnectionProtocol` interface but
returns canned responses and does not persist data.  This makes it useful for
unit tests that exercise database-dependent code paths without requiring an
actual database server.

## Intended Usage

- Unit tests where database behaviour needs to be simulated.
- Prototyping components that expect a `ConnectionProtocol` implementation.

## Limitations

- No SQL parsing or validation is performed.
- All query methods return empty results and all command methods report zero
  affected rows.
- The mock is not thread-safe and should not be used in production.

Refer to `tests/database/test_mock_database.py` for basic usage examples.
