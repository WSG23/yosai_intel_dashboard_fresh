from __future__ import annotations

import pytest
import sys
from pathlib import Path
import tests.infrastructure as infra_mod

from tests.infrastructure import MockFactory, TestInfrastructure


@pytest.fixture(scope="module")
def factory() -> MockFactory:
    with TestInfrastructure(MockFactory(), stub_packages=[]) as f:
        stubs_path = Path(infra_mod.__file__).resolve().parents[1] / "stubs"
        if str(stubs_path) in sys.path:
            sys.path.remove(str(stubs_path))
        yield f


def test_direct_processing_helper(factory: MockFactory, tmp_path):
    df1 = factory.dataframe(
        {
            "Timestamp": ["2024-01-01 10:00:00"],
            "Person ID": ["u1"],
            "Token ID": ["t1"],
            "Device name": ["d1"],
            "Access result": ["Granted"],
        }
    )
    proc = factory.upload_processor()
    result = proc._process_uploaded_data_directly({"f1.csv": df1})
    assert result["rows"] == 1
    assert result["columns"] == 5
