from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class ProcessingResult:
    """Unified result returned by mapping processors."""

    data: pd.DataFrame
    suggestions: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    success: bool = True
    errors: List[str] = field(default_factory=list)


@dataclass
class MappingData:
    """Aggregated results for a processed upload."""

    columns: ProcessingResult
    devices: ProcessingResult
