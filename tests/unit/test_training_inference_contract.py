from __future__ import annotations

from yosai_intel_dashboard.models.ml.pipeline_contract import preprocess_events as contract_preprocess
from yosai_intel_dashboard.models.ml.feature_pipeline import (
    preprocess_events as feature_preprocess,
)
from yosai_intel_dashboard.src.models.ml.training.pipeline import (
    preprocess_events as training_preprocess,
)


def test_training_and_inference_share_preprocess_contract():
    assert training_preprocess is contract_preprocess
    assert feature_preprocess is contract_preprocess
