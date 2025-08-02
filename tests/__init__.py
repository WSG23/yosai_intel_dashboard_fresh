from . import config  # noqa: F401 - ensure test configuration executes

pytest_plugins = ["tests.performance_plugin"]
