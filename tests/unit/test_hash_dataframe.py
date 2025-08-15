import importlib.util
from pathlib import Path

import pandas as pd

spec = importlib.util.spec_from_file_location(
    "utils.hashing", Path(__file__).resolve().parents[1] / "utils" / "hashing.py"
)
hashing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hashing)


def test_hash_dataframe_consistent():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    expected = df.to_csv(index=False).encode()
    import hashlib

    expected_hash = hashlib.sha256(expected).hexdigest()
    assert hashing.hash_dataframe(df) == expected_hash
