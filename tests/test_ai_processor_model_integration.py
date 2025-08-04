import importlib.machinery
import importlib.util
import sys

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from yosai_intel_dashboard.src.services.mapping.models import RuleBasedModel
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

# Insert stub before importing the adapter
stub = importlib.util.module_from_spec(
    importlib.machinery.ModuleSpec("components.plugin_adapter", None)
)
stub.ComponentPluginAdapter = object
safe_import('components.plugin_adapter', stub)

from yosai_intel_dashboard.src.services.mapping.processors.ai_processor import AIColumnMapperAdapter


def test_ai_processor_uses_mapping_model():

    container = ServiceContainer()
    model = RuleBasedModel({"A": "timestamp"})
    container.register_singleton("mapping_model", model)

    adapter = AIColumnMapperAdapter(container=container)
    df = pd.DataFrame({"A": [1]})
    result = adapter.suggest(df, "f.csv")
    assert result["A"]["field"] == "timestamp"

    # cached call should use same result
    result2 = adapter.suggest(df, "f.csv")
    assert result2 == result
