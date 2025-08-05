import pytest

from yosai_intel_dashboard.src.infrastructure.security.threat_intelligence import (
    AutomatedResponseOrchestrator,
    ThreatIntelligenceSystem,
)


@pytest.mark.asyncio
async def test_responses_are_queued(monkeypatch):
    system = ThreatIntelligenceSystem()
    orchestrator = AutomatedResponseOrchestrator()

    async def fake_gather():
        return [{"indicator": "malware"}]

    async def fake_correlate(data):
        assert data == [{"indicator": "malware"}]
        return [{"action": "isolate"}]

    monkeypatch.setattr(system, "gather_external_feeds", fake_gather)
    monkeypatch.setattr(system, "correlate_internal_patterns", fake_correlate)

    recorded = []

    def fake_create_task(coro):
        recorded.append(coro)
        if hasattr(coro, "close"):
            coro.close()
        return f"tid-{len(recorded)}"

    monkeypatch.setattr("asyncio.create_task", fake_create_task)

    feeds = await system.gather_external_feeds()
    corrs = await system.correlate_internal_patterns(feeds)
    await orchestrator.orchestrate_responses(corrs)

    assert len(recorded) == len(corrs)
    assert orchestrator.queued_actions == ["tid-1"]
