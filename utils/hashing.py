"""Hashing utilities."""

from __future__ import annotations

import hashlib

import pandas as pd


def hash_dataframe(df: pd.DataFrame) -> str:
    """Return SHA256 hash of ``df`` serialized as CSV.

    Parameters
    ----------
    df:
        DataFrame to hash.

    Returns
    -------
    str
        SHA256 hex digest of the DataFrame contents.
    """
    csv_bytes = df.to_csv(index=False).encode()
    return hashlib.sha256(csv_bytes).hexdigest()


__all__ = ["hash_dataframe"]
