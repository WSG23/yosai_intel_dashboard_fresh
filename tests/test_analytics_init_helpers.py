import types
import importlib.util
from pathlib import Path
import sys

# Stub heavy modules required by helpers
mods = {
    "services.analytics.upload_analytics": types.ModuleType("services.analytics.upload_analytics"),
    "services.controllers.upload_controller": types.ModuleType("services.controllers.upload_controller"),
    "services.chunked_analysis": types.ModuleType("services.chunked_analysis"),
    "services.database_retriever": types.ModuleType("services.database_retriever"),
    "services.analytics.calculator": types.ModuleType("services.analytics.calculator"),
    "services.analytics.data.loader": types.ModuleType("services.analytics.data.loader"),
    "services.analytics.publisher": types.ModuleType("services.analytics.publisher"),
}
analytics_pkg = types.ModuleType("services.analytics")
analytics_pkg.__path__ = []
sys.modules.setdefault("services.analytics", analytics_pkg)

protocols_mod = types.ModuleType("services.analytics.protocols")
class DataProcessorProtocol: ...
protocols_mod.DataProcessorProtocol = DataProcessorProtocol
sys.modules.setdefault("services.analytics.protocols", protocols_mod)

orchestrator_mod = types.ModuleType("services.analytics.orchestrator")
class AnalyticsOrchestrator:
    def __init__(self, *a, **k): ...
orchestrator_mod.AnalyticsOrchestrator = AnalyticsOrchestrator
sys.modules.setdefault("services.analytics.orchestrator", orchestrator_mod)
analytics_pkg.protocols = protocols_mod
analytics_pkg.orchestrator = orchestrator_mod
if "UploadAnalyticsProcessor" not in mods["services.analytics.upload_analytics"].__dict__:
    class UploadAnalyticsProcessor:
        def __init__(self, *a, **k): ...
    mods["services.analytics.upload_analytics"].UploadAnalyticsProcessor = UploadAnalyticsProcessor

if "UploadProcessingController" not in mods["services.controllers.upload_controller"].__dict__:
    class UploadProcessingController:
        def __init__(self, *a, **k): ...
    mods["services.controllers.upload_controller"].UploadProcessingController = UploadProcessingController

class Calculator: ...
class DataLoader:
    def __init__(self, *a, **k): ...
class Publisher:
    def __init__(self, *a, **k): ...
class DatabaseAnalyticsRetriever: ...
mods["services.analytics.calculator"].Calculator = Calculator
mods["services.analytics.data.loader"].DataLoader = DataLoader
mods["services.analytics.publisher"].Publisher = Publisher
mods["services.database_retriever"].DatabaseAnalyticsRetriever = DatabaseAnalyticsRetriever
mods["services.analytics.calculator"].create_calculator = lambda: Calculator()
sys.modules.setdefault("dash.dash", sys.modules.get("dash"))

for name, mod in mods.items():
    sys.modules.setdefault(name, mod)

spec = importlib.util.spec_from_file_location(
    "analytics_helpers", Path("services/analytics/helpers.py")
)
helpers = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(helpers)
initialize_core_components = helpers.initialize_core_components
initialize_orchestrator_components = helpers.initialize_orchestrator_components
DataSourceRouter = helpers.DataSourceRouter
from services.summary_report_generator import SummaryReportGenerator
from services.data_processing.processor import Processor
from validation.security_validator import SecurityValidator


def test_initialize_core_components_defaults():
    svc = types.SimpleNamespace()
    initialize_core_components(
        svc,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    )
    assert isinstance(svc.validation_service, SecurityValidator)
    assert isinstance(svc.processor, Processor)
    assert svc.upload_controller is not None
    assert svc.upload_processor is not None
    assert isinstance(svc.report_generator, SummaryReportGenerator)


def test_initialize_orchestrator_components(monkeypatch):
    svc = types.SimpleNamespace()
    records = {}
    svc.upload_controller = object()
    svc.processor = object()
    svc.report_generator = SummaryReportGenerator()
    svc.event_bus = None

    def fake_setup(db=None):
        records['setup'] = True
    def fake_create(loader, calc, pub):
        records['create'] = True
    svc._setup_database = fake_setup
    svc._create_orchestrator = fake_create

    initialize_orchestrator_components(svc)
    assert records.get('setup') and records.get('create')
    assert isinstance(svc.router, DataSourceRouter)

