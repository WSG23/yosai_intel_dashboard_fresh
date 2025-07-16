class Process:
    def __init__(self, *a, **k):
        pass

    def cpu_percent(self, interval=None):
        return 0

    def memory_info(self):
        return type("mem", (), {"rss": 0})()
