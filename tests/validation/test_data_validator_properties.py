"""Property based tests for :class:`DataValidator`."""

import string
import sys
import types

import pandas as pd
from hypothesis import given, strategies as st

from validation.data_validator import DataValidator, SuspiciousColumnNameRule
import hypothesis.internal.conjecture.providers as hp

def _noop_local_constants() -> hp.Constants:
    return hp._local_constants

hp._get_local_constants = _noop_local_constants  # type: ignore

for mod in ("typing.io", "typing.re"):
    obj = sys.modules.get(mod)
    if isinstance(obj, types.SimpleNamespace):
        sys.modules[mod] = types.ModuleType(mod)


def _non_suspicious_names():
    pattern = SuspiciousColumnNameRule.DEFAULT_PATTERN
    base = st.text(alphabet=string.ascii_letters, min_size=1, max_size=5)
    return base.filter(lambda s: not pattern.search(s))


@st.composite
def df_with_required(draw):
    """Generate DataFrames containing required columns ``foo`` and ``bar``."""

    rows = draw(st.integers(min_value=1, max_value=5))
    data: dict[str, list[int]] = {
        "foo": draw(st.lists(st.integers(), min_size=rows, max_size=rows)),
        "bar": draw(st.lists(st.integers(), min_size=rows, max_size=rows)),
    }

    extra_cols = draw(
        st.lists(_non_suspicious_names(), min_size=0, max_size=3, unique=True)
        .filter(lambda cols: not {"foo", "bar"} & set(cols))
    )
    for name in extra_cols:
        data[name] = draw(st.lists(st.integers(), min_size=rows, max_size=rows))

    return pd.DataFrame(data)


@st.composite
def df_with_suspicious(draw):
    """Generate DataFrames containing at least one suspicious column."""

    rows = draw(st.integers(min_value=1, max_value=5))
    suspicious_names = [
        "cmd",
        "system",
        "delete",
        "drop",
        "exec",
        "=1",
        "+foo",
        "@bar",
    ]
    chosen = draw(st.lists(st.sampled_from(suspicious_names), min_size=1, max_size=3, unique=True))
    safe = draw(st.lists(_non_suspicious_names(), min_size=0, max_size=2, unique=True))
    names = chosen + [n for n in safe if n not in chosen]

    data = {
        name: draw(st.lists(st.integers(), min_size=rows, max_size=rows))
        for name in names
    }
    return pd.DataFrame(data)


@given(df=df_with_required())
def test_required_columns_are_valid(df: pd.DataFrame) -> None:
    result = DataValidator(required_columns=["foo", "bar"]).validate_dataframe(df)
    assert result.valid


@given(df=df_with_suspicious())
def test_suspicious_columns_reported(df: pd.DataFrame) -> None:
    result = DataValidator().validate_dataframe(df)
    assert not result.valid
    assert any("suspicious_columns" in issue for issue in result.issues)

