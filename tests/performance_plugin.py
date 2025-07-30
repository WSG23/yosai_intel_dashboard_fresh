import inspect

import pytest

DURATION_TOTAL: dict[str, float] = {}
DURATION_COUNT: dict[str, int] = {}


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    if report.when == "call":
        DURATION_TOTAL.setdefault(report.nodeid, 0.0)
        DURATION_COUNT.setdefault(report.nodeid, 0)
        DURATION_TOTAL[report.nodeid] += report.duration
        DURATION_COUNT[report.nodeid] += 1


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    slow = []
    for nodeid, total in DURATION_TOTAL.items():
        avg = total / max(DURATION_COUNT.get(nodeid, 1), 1)
        if avg > 0.05:
            slow.append((nodeid, avg))

    if slow:
        reporter = session.config.pluginmanager.getplugin("terminalreporter")
        if reporter:
            reporter.write_line("Performance failures:")
            for nodeid, avg in slow:
                reporter.write_line(f" {nodeid} took {avg*1000:.2f} ms on average")
        session.exitstatus = 1


def pytest_collection_finish(session: pytest.Session) -> None:
    offenders = []
    for item in session.items:
        try:
            src = inspect.getsource(item.function)
        except OSError:
            continue
        if "sys.modules" in src:
            offenders.append(item.nodeid)

    if offenders:
        lines = "\n".join(offenders)
        raise pytest.UsageError("sys.modules manipulation detected in tests:\n" + lines)
