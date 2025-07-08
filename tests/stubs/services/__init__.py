from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)


def get_analytics_service():
    class Svc:
        def health_check(self):
            return "ok"

    return Svc()
