import logging

import pages


def test_missing_page_logs_error(monkeypatch, caplog):
    monkeypatch.setitem(pages.PAGE_MODULES, "missing", "pages.missing_page")
    pages.clear_page_cache()
    with caplog.at_level("ERROR"):
        module = pages._load_page("missing")
    assert module is None
    assert any(
        "Failed to import page missing" in record.getMessage()
        for record in caplog.records
    )
