from yosai_intel_dashboard.src.services.upload.learning_coordinator import LearningCoordinator
from tests.fakes import FakeDeviceLearningService
from tests.utils.builders import DataFrameBuilder


def test_learning_coordinator_user_mappings():
    svc = FakeDeviceLearningService()
    svc.saved["f.csv"] = {"dev": {}}
    coord = LearningCoordinator(svc)
    assert coord.user_mappings("f.csv") == {"dev": {}}


def test_learning_coordinator_auto_apply():
    svc = FakeDeviceLearningService()
    coord = LearningCoordinator(svc)
    df = DataFrameBuilder().add_column("a", [1]).build()
    assert coord.auto_apply(df, "f.csv") is False
