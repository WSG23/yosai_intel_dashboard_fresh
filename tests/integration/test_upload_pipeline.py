from __future__ import annotations

import pytest

from tests.infrastructure import MockFactory, TestInfrastructure

# Prepare a lightweight environment using shared test infrastructure
infra = TestInfrastructure(
    stub_packages=["pandas", "numpy", "yaml"]
).setup_environment()  # noqa: F841


@pytest.fixture
def valid_df():
    return MockFactory.dataframe(
        {"Person ID": ["u1", "u2"], "Device name": ["d1", "d2"]}
    )


@pytest.fixture
def uploaded_data(valid_df):
    from tests.stubs.utils.upload_store import get_uploaded_data_store

    store = get_uploaded_data_store()
    store.clear_all()
    store.data["empty.csv"] = MockFactory.dataframe({})
    store.data["valid.csv"] = valid_df
    return store.get_all_data()


@pytest.fixture
def upload_processor(uploaded_data):
    return MockFactory.upload_processor()


def test_upload_pipeline_filters_empty_and_returns_stats(upload_processor):
    result = upload_processor.analyze_uploaded_data()

    # Final statistics should reflect only the valid data
    assert result["status"] == "success"
    assert result["rows"] == 2
    assert result["columns"] == 2
