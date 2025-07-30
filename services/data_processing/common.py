"""Common dataframe processing utilities."""

from __future__ import annotations

from typing import Optional, Tuple

import pandas as pd

from config.dynamic_config import dynamic_config
from core.protocols import ConfigurationProtocol

from .dataframe_utils import process_dataframe as _process_dataframe


def process_dataframe(
    decoded: bytes,
    filename: str,
    *,
    config: ConfigurationProtocol = dynamic_config,
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    return _process_dataframe(decoded, filename, config=config)
