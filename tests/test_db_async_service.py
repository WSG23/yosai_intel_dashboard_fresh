import asyncio

from src.services.database.analytics_service import AnalyticsService


class Conn:
    def execute_query(self, query):
        if "COUNT" in query:
            return [{"count": 1}]
        return [
            {"event_type": "login", "status": "success", "timestamp": "2024-01-01"}
        ]


class Manager:
    def health_check(self):
        return True

    def get_connection(self):
        return Conn()

    def release_connection(self, conn):
        pass


def test_get_analytics_async():
    service = AnalyticsService(Manager())
    result = asyncio.run(service.get_analytics())
    assert result["status"] == "success"
    assert result["data"]["user_count"] == 1
