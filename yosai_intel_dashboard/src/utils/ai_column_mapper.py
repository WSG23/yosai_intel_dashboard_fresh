"""AI-assisted column mapping with fuzzy standardization."""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from yosai_intel_dashboard.src.components.plugin_adapter import ComponentPluginAdapter
from yosai_intel_dashboard.src.mapping.models import ColumnRules, load_rules

# ---------------------------------------------------------------------------
# Header variant dictionaries
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Standardization helpers
# ---------------------------------------------------------------------------


def standardize_column_names(
    df: pd.DataFrame,
    rules: ColumnRules | None = None,
    custom_mappings: Optional[Dict[str, List[str]]] = None,
    use_japanese: bool = False,
) -> pd.DataFrame:
    """Return ``df`` with columns renamed to canonical headers."""

    rules = rules or load_rules()
    mappings: Dict[str, List[str]] = {**rules.english}
    if use_japanese:
        for key, vals in rules.japanese.items():
            mappings.setdefault(key, []).extend(vals)
    if custom_mappings:
        for key, vals in custom_mappings.items():
            mappings.setdefault(key, []).extend(vals)

    reverse: Dict[str, str] = {}
    for canon, aliases in mappings.items():
        reverse[canon.lower()] = canon
        for alias in aliases:
            reverse[str(alias).lower()] = canon

    renamed: Dict[str, str] = {}
    for col in df.columns:
        target = reverse.get(str(col).lower())
        if target:
            renamed[col] = target

    if renamed:
        df = df.rename(columns=renamed)
    return df


class AIColumnMapperAdapter:
    """Combine AI suggestions with fuzzy header standardization."""

    def __init__(
        self,
        ai_adapter: ComponentPluginAdapter,
        custom_mappings: Optional[Dict[str, List[str]]] = None,
        use_japanese: bool = False,
        rules: ColumnRules | None = None,
    ) -> None:
        self.ai_adapter = ai_adapter
        self.custom_mappings = custom_mappings
        self.use_japanese = use_japanese
        self.rules = rules or load_rules()

    def map_and_standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        suggestions = self.ai_adapter.suggest_columns(df)
        df = df.rename(columns=suggestions)
        return standardize_column_names(
            df,
            rules=self.rules,
            custom_mappings=self.custom_mappings,
            use_japanese=self.use_japanese,
        )


if __name__ == "__main__":
    import pandas as pd
    from example_ai_adapter import ComponentPluginAdapter

    data = {
        "Time": ["2023-01-01 12:00"],
        "利用者ID": ["A1"],
        "Door Name": ["D1"],
        "結果": ["Granted"],
    }
    frame = pd.DataFrame(data)
    mapper = AIColumnMapperAdapter(ComponentPluginAdapter(), use_japanese=True)
    result = mapper.map_and_standardize(frame)
    print(result.columns.tolist())
