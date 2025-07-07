from typing import Optional, Dict, List

import numpy as np
import pandas as pd

from column_mapper import AIColumnMapperAdapter
from example_ai_adapter import ComponentPluginAdapter

CONTROL_CHAR_PATTERN = r"[\x00-\x1F\x7F]"


def load_raw_file(path: str) -> pd.DataFrame:
    """Load raw file as DataFrame supporting CSV, JSON and Excel."""
    lower = path.lower()
    if lower.endswith('.csv'):
        return pd.read_csv(path)
    if lower.endswith('.json'):
        return pd.read_json(path)
    if lower.endswith(('.xlsx', '.xls')):
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file type: {path}")


def validate_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Validate each row and append ``is_valid`` and ``validation_errors``.

    Rules applied per row:
      - ``MISSING_REQUIRED``: any of ``timestamp``, ``person_id``, ``door_id`` or
        ``access_result`` is null.
      - ``TOO_MANY_EMPTY``: ratio of empty cells exceeds ``0.5``.
      - ``CONTROL_CHAR_EXCEEDED``: control-character ratio exceeds ``0.1``.

    The function retains all rows and simply marks invalid ones.
    """

    df = df.copy()
    required = ["timestamp", "person_id", "door_id", "access_result"]

    req_df = pd.concat(
        [
            df[col]
            if col in df.columns
            else pd.Series([pd.NA] * len(df), index=df.index)
            for col in required
        ],
        axis=1,
    )
    missing_required = req_df.isna().any(axis=1)

    empty_ratio = df.isna().sum(axis=1) / df.shape[1]
    too_many_empty = empty_ratio > 0.5

    str_df = df.select_dtypes(include="object")
    if not str_df.empty:
        filled = str_df.fillna("")
        control_chars = filled.apply(lambda c: c.str.count(CONTROL_CHAR_PATTERN))
        control_count = control_chars.sum(axis=1)
        total_chars = filled.applymap(len).sum(axis=1)
        control_ratio = np.where(total_chars == 0, 0, control_count / total_chars)
    else:
        control_ratio = pd.Series(0, index=df.index)
    control_exceeded = control_ratio > 0.1

    is_valid = ~(missing_required | too_many_empty | control_exceeded)

    error_codes = [
        "MISSING_REQUIRED",
        "TOO_MANY_EMPTY",
        "CONTROL_CHAR_EXCEEDED",
    ]
    validation_errors = [
        [code for cond, code in zip(
            (missing_required[i], too_many_empty[i], control_exceeded[i]),
            error_codes,
        ) if cond]
        for i in range(len(df))
    ]

    df["is_valid"] = is_valid
    df["validation_errors"] = validation_errors
    return df


def process_file(
    path: str,
    custom_mappings: Optional[Dict[str, List[str]]] = None,
    use_japanese: bool = False
) -> pd.DataFrame:
    """Load and process a file applying AI-assisted column mapping."""
    df_raw = load_raw_file(path)

    ai_adapter = ComponentPluginAdapter()
    mapper = AIColumnMapperAdapter(
        ai_adapter,
        custom_mappings=custom_mappings,
        use_japanese=use_japanese
    )
    df_raw = mapper.map_and_standardize(df_raw)

    df_validated = validate_rows(df_raw)

    # Further validation, enrichment, anomaly detection would continue here.
    return df_validated
