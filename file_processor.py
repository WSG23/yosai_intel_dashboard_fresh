from typing import Optional, Dict, List
import pandas as pd

from column_mapper import AIColumnMapperAdapter
from example_ai_adapter import ComponentPluginAdapter


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

    # Further validation, enrichment, anomaly detection would continue here.
    return df_raw
