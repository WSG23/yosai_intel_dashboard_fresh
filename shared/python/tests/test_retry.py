import pytest

from shared.python.retry import retry, RetryError


def test_retry_exhausts():
    attempts = []

    def bad():
        attempts.append(1)
        raise RuntimeError("boom")

    with pytest.raises(RetryError):
        retry(bad, attempts=2)
    assert len(attempts) == 2
