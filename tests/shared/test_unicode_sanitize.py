from shared.python.unicode_sanitize import clean_surrogates


def test_clean_surrogates_replaces():
    text = "\ud800A\udfff"
    assert clean_surrogates(text) == "\uFFFDA\uFFFD"


def test_clean_surrogates_no_change():
    text = "regular"
    assert clean_surrogates(text) == text
