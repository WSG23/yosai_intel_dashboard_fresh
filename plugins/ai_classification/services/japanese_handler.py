"""Japanese text handling utilities"""

import re
from typing import Any

from yosai_intel_dashboard.src.adapters.api.plugins.ai_classification.config import (
    JapaneseConfig,
)


class JapaneseTextHandler:
    def __init__(self, config: JapaneseConfig) -> None:
        self.config = config

    def detect_japanese(self, text: str) -> bool:
        return bool(re.search("[\u3040-\u30ff\u4e00-\u9faf]", text))

    def normalize_text(self, text: str) -> str:
        return text.strip()
