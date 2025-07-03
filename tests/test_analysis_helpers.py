import pandas as pd
import dash_bootstrap_components as dbc

from utils.analysis_helpers import build_ai_suggestions, render_results_card


def test_build_ai_suggestions_basic():
    df = pd.DataFrame({"Time": [1, 2, 3], "Person": ["a", "b", "c"]})
    suggestions, avg, confident = build_ai_suggestions(df)
    assert len(suggestions) == 2 or len(suggestions) == 3
    assert avg >= 0
    assert confident >= 0


def test_render_results_card_simple():
    results = {
        "total_events": 10,
        "unique_users": {"u1", "u2"},
        "unique_doors": {"d1"},
        "successful_events": 8,
        "failed_events": 2,
        "security_score": {"score": 80, "threat_level": "low"},
    }
    card = render_results_card(results, "security")
    assert isinstance(card, dbc.Card)
