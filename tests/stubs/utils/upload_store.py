from __future__ import annotations

from tests.unit.fakes import FakeUploadStore

_fake_store = FakeUploadStore()
uploaded_data_store = _fake_store


def get_uploaded_data_store() -> FakeUploadStore:
    return _fake_store
