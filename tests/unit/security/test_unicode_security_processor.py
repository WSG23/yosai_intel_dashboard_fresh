from yosai_intel_dashboard.src.core.unicode import sanitize_unicode_input


def test_sanitize_unicode_removes_surrogates_and_normalizes():
    text = "test" + "\ud83d\ude00"  # 😀 surrogate pair
    result = sanitize_unicode_input(text)
    assert result == "test"  # emoji removed

    # normalization example - fullwidth digits
    fullwidth = "１２３"
    assert sanitize_unicode_input(fullwidth) == "123"


def test_sanitize_unicode_handles_unpaired_surrogate():
    text = "bad" + "\ud800"
    result = sanitize_unicode_input(text)
    assert result == "bad"
