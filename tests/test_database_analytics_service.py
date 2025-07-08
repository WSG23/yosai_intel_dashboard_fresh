from typing import Protocol

from services.database_analytics_service import DatabaseAnalyticsService


class ConnectionProtocol(Protocol):
    def execute_query(self, query, params=None): ...


class FakeConnection(ConnectionProtocol):
    def execute_query(self, query, params=None):
        if "GROUP BY event_type, status" in query:
            return [
                {"event_type": "access", "status": "success", "count": 80},
                {"event_type": "access", "status": "failure", "count": 20},
            ]
        if "strftime('%H'" in query:
            return [
                {"hour": "08", "event_count": 50},
                {"hour": "09", "event_count": 50},
            ]
        if "GROUP BY location" in query:
            return [
                {"location": "A", "total_events": 60, "successful_events": 50},
                {"location": "B", "total_events": 40, "successful_events": 30},
            ]
        return []


class DBManagerProtocol(Protocol):
    def get_connection(self) -> ConnectionProtocol: ...


class FakeDBManager(DBManagerProtocol):
    def get_connection(self):
        return FakeConnection()


def test_database_analytics_basic():
    service = DatabaseAnalyticsService(FakeDBManager())
    result = service.get_analytics()
    assert result["status"] == "success"
    assert result["summary"]["total_events"] == 100
    assert result["summary"]["success_rate"] == 80.0
    assert result["location_stats"]["busiest_location"] == "A"
