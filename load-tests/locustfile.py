from __future__ import annotations

from locust import HttpUser, SequentialTaskSet, between, task


class AnalyticsJourney(SequentialTaskSet):
    """User journey hitting common analytics endpoints sequentially."""

    @task
    def dashboard_summary(self):
        self.client.get("/api/v1/analytics/dashboard-summary")

    @task
    def access_patterns(self):
        self.client.get("/api/v1/analytics/access-patterns")

    @task
    def stop(self):
        # Finish the journey
        self.interrupt()


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    tasks = {AnalyticsJourney: 5}

    @task(1)
    def health(self):
        self.client.get("/health")
