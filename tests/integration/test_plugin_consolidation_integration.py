import pandas as pd

from core.container import Container as DIContainer
from core.plugins.manager import PluginManager
from core.plugins.protocols import PluginMetadata
from config.config import ConfigManager
from services.consolidated_learning_service import ConsolidatedLearningService


class LearningPlugin:
    metadata = PluginMetadata(
        name="learning",
        version="0.1",
        description="learning plugin",
        author="tester",
    )

    def __init__(self):
        self.service = None

    def load(self, container, config):
        self.service = ConsolidatedLearningService()
        container.register("learning_service", self.service)
        return True

    def configure(self, config):
        return True

    def start(self):
        return True

    def stop(self):
        return True

    def health_check(self):
        return {"healthy": True}


def test_plugin_learning_service(tmp_path, monkeypatch):
    # Provide required secrets so ConfigManager does not fail
    for key in [
        "SECRET_KEY",
        "DB_PASSWORD",
        "AUTH0_CLIENT_ID",
        "AUTH0_CLIENT_SECRET",
        "AUTH0_DOMAIN",
        "AUTH0_AUDIENCE",
    ]:
        monkeypatch.setenv(key, "x")

    container = DIContainer()
    manager = PluginManager(container, ConfigManager(), health_check_interval=1)
    plugin = LearningPlugin()
    assert manager.load_plugin(plugin)
    service = container.get("learning_service")
    df = pd.DataFrame({"door_id": ["d1"], "timestamp": ["2024-01-01"]})
    fp = service.save_complete_mapping(df, "file.csv", {"d1": {"floor": 1}})
    learned = service.get_learned_mappings(df, "file.csv")
    assert learned["match_type"] == "exact"
    assert fp in service.learned_data
    manager.stop_all_plugins()
    manager.stop_health_monitor()
