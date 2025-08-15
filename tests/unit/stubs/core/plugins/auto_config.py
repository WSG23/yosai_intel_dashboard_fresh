from types import SimpleNamespace


class PluginAutoConfiguration:
    def __init__(self, app, *, container=None, config_manager=None, package="plugins"):
        self.app = app
        self.container = container
        self.config_manager = config_manager
        self.package = package

        class PM:
            def stop_all_plugins(self):
                self.stopped = True

            def stop_health_monitor(self):
                self.monitor_stopped = True

        self.registry = SimpleNamespace(plugin_manager=PM())
        self.scanned = None
        self.generated = False

    def scan_and_configure(self, pkg):
        self.scanned = pkg

    def generate_health_endpoints(self):
        self.generated = True
