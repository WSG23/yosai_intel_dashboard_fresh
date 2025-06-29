class Flask:
    def __init__(self, name):
        self.name = name
        self.url_map = _UrlMap()
        self.server = self

    def route(self, rule, methods=None):
        def decorator(func):
            self.url_map.add(rule)
            return func
        return decorator

class _UrlMap:
    def __init__(self):
        self._rules = []

    def add(self, rule):
        self._rules.append(rule)

    def iter_rules(self):
        for r in self._rules:
            yield r
