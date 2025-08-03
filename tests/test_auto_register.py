from __future__ import annotations

import pytest
from pydantic import ValidationError

from yosai_intel_dashboard.src.mapping.models import (
    MODEL_REGISTRY,
    HeuristicMappingModel,
    MappingModel,
    MLMappingModel,
    RuleBasedModel,
    get_registered_model,
)


def test_models_auto_registered():
    assert get_registered_model("heuristic") is HeuristicMappingModel
    assert get_registered_model("rule_based") is RuleBasedModel
    assert get_registered_model("ml") is MLMappingModel
    assert "heuristic" in MODEL_REGISTRY
    assert "rule_based" in MODEL_REGISTRY
    assert "ml" in MODEL_REGISTRY


def test_autoregister_validation():
    with pytest.raises(ValidationError):

        class BadModel(MappingModel):
            registry_name = ""  # invalid empty name

            def suggest(self, df, filename):  # type: ignore[override]
                return {}
