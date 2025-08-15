from types import SimpleNamespace
from unittest.mock import patch

import pathlib
import sys

import pytest

# ensure repository root is importable for analytics module
sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))

from analytics.context_providers import (
    ContextProviderError,
    fetch_local_events,
    fetch_social_signals,
)


def test_fetch_local_events_invalid_city() -> None:
    with pytest.raises(ValueError):
        fetch_local_events("<script>")


def test_fetch_social_signals_invalid_topic() -> None:
    with pytest.raises(ValueError):
        fetch_social_signals("bad!topic")


def test_fetch_local_events_bad_content_type() -> None:
    fake_resp = SimpleNamespace(
        headers={"Content-Type": "text/html"},
        content=b"{}",
        json=lambda: {"events": []},
        raise_for_status=lambda: None,
    )
    with patch("analytics.context_providers.requests.get", return_value=fake_resp), \
        patch.dict("analytics.context_providers.os.environ", {"EVENTS_API_URL": "http://x"}):
        with pytest.raises(ContextProviderError):
            fetch_local_events("City")
