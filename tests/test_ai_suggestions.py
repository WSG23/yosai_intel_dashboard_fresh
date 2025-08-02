import pytest

from yosai_intel_dashboard.src.services.data_enhancer.mapping_utils import get_ai_column_suggestions


def test_basic_suggestions():
    columns = ["Time", "Person ID", "Token ID", "Door Name", "Result", "Other"]
    suggestions = get_ai_column_suggestions(columns)
    assert suggestions["Time"]["field"] == "timestamp"
    assert suggestions["Person ID"]["field"] == "person_id"
    assert suggestions["Token ID"]["field"] == "token_id"
    assert suggestions["Door Name"]["field"] == "door_id"
    assert suggestions["Result"]["field"] == "access_result"
    assert suggestions["Other"]["field"] == ""


def test_unknown_column_returns_empty():
    suggestions = get_ai_column_suggestions(["Mystery"])
    assert suggestions["Mystery"]["field"] == ""
    assert suggestions["Mystery"]["confidence"] == 0.0
