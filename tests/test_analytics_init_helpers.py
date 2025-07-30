import types
import importlib.util
from pathlib import Path

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

