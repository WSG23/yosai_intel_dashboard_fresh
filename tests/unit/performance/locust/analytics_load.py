"""Locust tasks for analytics query load testing."""

from locust import HttpUser, between, task

from .utils import random_user_id


class AnalyticsQueryUser(HttpUser):
    """Simulate heavy analytics queries from multiple users."""

    wait_time = between(0.1, 0.5)

    @task
    def query_analytics(self) -> None:
        user = random_user_id()
        self.client.get(f"/analytics/query?user_id={user}", name="GET /analytics/query")
