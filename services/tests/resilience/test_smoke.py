"""Smoke tests for the services.resilience package."""


def test_circuit_breaker_import() -> None:
    """Ensure CircuitBreaker class can be imported."""
    from services.resilience import CircuitBreaker

    assert CircuitBreaker.__name__ == "CircuitBreaker"
