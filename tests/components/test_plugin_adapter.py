import pandas as pd
from components.plugin_adapter import ComponentPluginAdapter
import components.plugin_adapter as plugin_adapter
from utils.unicode_utils import sanitize_dataframe, clean_unicode_text


def test_get_ai_column_suggestions_with_plugin(monkeypatch):
    adapter = ComponentPluginAdapter()

    class Dummy:
        def map_columns(self, headers, session_id):
            return {
                "success": True,
                "suggested_mapping": {h: "field" for h in headers},
                "confidence_scores": {h: 0.8 for h in headers},
            }

    monkeypatch.setattr(
        plugin_adapter.PluginServiceLocator,
        "get_ai_classification_service",
        lambda: Dummy(),
    )
    df = pd.DataFrame(columns=["A", "B"])
    result = adapter.get_ai_column_suggestions(df, "f.csv")
    assert result["A"]["field"] == "field"
    assert result["A"]["confidence"] == 0.8


def test_get_ai_column_suggestions_fallback(monkeypatch):
    adapter = ComponentPluginAdapter()
    monkeypatch.setattr(
        plugin_adapter.PluginServiceLocator,
        "get_ai_classification_service",
        lambda: None,
    )
    df = pd.DataFrame(columns=["Mystery"])
    result = adapter.get_ai_column_suggestions(df, "x.csv")
    assert result["Mystery"]["field"] == ""


def test_unicode_helpers():
    df = pd.DataFrame({"col\uD83D": ["val\uDE00"]})
    out = sanitize_dataframe(df)
    assert "\uD83D" not in str(out.columns)
    assert "\uDE00" not in str(out.values)
    assert clean_unicode_text("t\uD83D") == "t"
