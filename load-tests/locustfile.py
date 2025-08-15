from __future__ import annotations

import os
import time

import gevent
from locust import (
    HttpUser,
    LoadTestShape,
    SequentialTaskSet,
    between,
    events,
    task,
)

try:
    import psutil
except Exception:  # pragma: no cover - psutil may not be installed in CI
    psutil = None


class AnalyticsJourney(SequentialTaskSet):
    """User journey hitting common analytics endpoints sequentially."""

    @task
    def dashboard_summary(self) -> None:
        self.client.get("/api/v1/analytics/dashboard-summary")

    @task
    def access_patterns(self) -> None:
        self.client.get("/api/v1/analytics/access-patterns")

    @task
    def threat_assessment(self) -> None:
        self.client.get("/api/v1/analytics/threat_assessment")

    @task
    def stop(self) -> None:
        # Finish the journey
        self.interrupt()


class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    tasks = {AnalyticsJourney: 5}

    @task(1)
    def health(self) -> None:
        self.client.get("/health")


class TrafficShape(LoadTestShape):
    """Parameterised load shape allowing burst and sustained scenarios."""

    def __init__(self) -> None:
        self.test_type = os.getenv("LOAD_TEST_TYPE", "sustained")
        self.burst_users = int(os.getenv("BURST_USERS", "100"))
        self.sustained_users = int(os.getenv("SUSTAINED_USERS", "50"))
        self.burst_duration = int(os.getenv("BURST_DURATION", "30"))
        self.sustained_duration = int(os.getenv("SUSTAINED_DURATION", "300"))

    def tick(self):  # pragma: no cover - called internally by Locust
        run_time = self.get_run_time()
        if self.test_type == "burst":
            if run_time < self.burst_duration:
                return self.burst_users, self.burst_users
            if run_time < self.burst_duration + self.sustained_duration:
                return self.sustained_users, self.sustained_users
            return None
        # Sustained load
        if run_time < self.sustained_duration:
            return self.sustained_users, self.sustained_users
        return None


if psutil:
    METRICS_FILE = os.getenv("METRICS_FILE", "system_metrics.csv")
    metrics_fh = open(METRICS_FILE, "w", buffering=1)
    metrics_fh.write("time,cpu_percent,memory_percent\n")

    def _capture_metrics(environment):  # pragma: no cover - side effect function
        while environment.runner and environment.runner.state != "stopped":
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            metrics_fh.write(f"{time.time()},{cpu},{mem}\n")
            gevent.sleep(1)

    @events.test_start.add_listener
    def on_test_start(environment, **_kw):  # pragma: no cover
        gevent.spawn(_capture_metrics, environment)

    @events.test_stop.add_listener
    def on_test_stop(environment, **_kw):  # pragma: no cover
        metrics_fh.close()
