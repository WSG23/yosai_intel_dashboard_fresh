"""Main Locust entrypoint for performance suite."""

from locust import LoadTestShape
from locust.env import Environment

from .analytics_load import AnalyticsQueryUser
from .events_load import EventIngestionUser


class RampUpShape(LoadTestShape):
    """Gradually ramp users then hold."""

    stages = [
        {"duration": 60, "users": 1000, "spawn_rate": 50},
        {"duration": 120, "users": 5000, "spawn_rate": 100},
        {"duration": 180, "users": 10000, "spawn_rate": 200},
    ]

    def tick(self):
        run_time = self.get_run_time()
        total = 0
        for stage in self.stages:
            total += stage["duration"]
            if run_time < total:
                return (stage["users"], stage["spawn_rate"])
        return None


# Locust uses Environment to register users when launched via CLI
class UserEnvironment(Environment):
    user_classes = [EventIngestionUser, AnalyticsQueryUser]
    shape_class = RampUpShape
