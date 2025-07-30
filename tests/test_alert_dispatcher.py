import asyncio

import pytest

from core.monitoring.user_experience_metrics import AlertConfig, AlertDispatcher


class DummyResp:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


class DummySession:
    def __init__(self, calls):
        self.calls = calls

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def post(self, url, json=None, timeout=None):
        self.calls.append((url, json))
        return DummyResp()


class DummySMTP:
    def __init__(self, hostname="localhost"):
        self.hostname = hostname
        self.sent = []

    async def connect(self):
        pass

    async def sendmail(self, from_addr, to_addrs, message):
        self.sent.append((from_addr, to_addrs, message))

    async def quit(self):
        pass


@pytest.mark.asyncio
async def test_send_alert_async(monkeypatch):
    calls = []
    monkeypatch.setattr("aiohttp.ClientSession", lambda: DummySession(calls))
    monkeypatch.setattr(
        "aiosmtplib.SMTP", lambda hostname="localhost": DummySMTP(hostname)
    )

    dispatcher = AlertDispatcher(
        AlertConfig(
            slack_webhook="http://slack",
            webhook_url="http://wh",
            email="a@b.com",
        )
    )
    await dispatcher.send_alert_async("hi")

    assert ("http://slack", {"text": "hi"}) in calls
    assert ("http://wh", {"message": "hi"}) in calls


def test_send_alert_sync_fallback(monkeypatch):
    calls = []

    def dummy_post(url, json=None, timeout=None):
        calls.append((url, json))

        class Resp:
            pass

        return Resp()

    class DummySMTPBlocking:
        def __init__(self, hostname="localhost"):
            self.hostname = hostname

        def sendmail(self, from_addr, to_addrs, message):
            calls.append(("sendmail", from_addr, to_addrs, message))

        def quit(self):
            pass

    monkeypatch.setattr("requests.post", dummy_post)
    monkeypatch.setattr("smtplib.SMTP", lambda host: DummySMTPBlocking(host))
    monkeypatch.setattr(
        "aiohttp.ClientSession",
        lambda: (_ for _ in ()).throw(AssertionError("async called")),
    )
    monkeypatch.setattr(
        "aiosmtplib.SMTP",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("async called")),
    )

    class Loop:
        def is_running(self):
            return True

    monkeypatch.setattr(asyncio, "get_running_loop", lambda: Loop())

    dispatcher = AlertDispatcher(
        AlertConfig(
            slack_webhook="http://slack",
            webhook_url="http://wh",
            email="a@b.com",
        )
    )
    dispatcher.send_alert("hello")

    assert ("http://slack", {"text": "hello"}) in calls
    assert ("http://wh", {"message": "hello"}) in calls
    assert ("sendmail", "noreply@example.com", ["a@b.com"], "hello") in calls
