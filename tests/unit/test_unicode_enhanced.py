import pytest

from yosai_intel_dashboard.src.core.unicode import (
    EnhancedUnicodeProcessor,
    SurrogateHandlingConfig,
    SurrogateHandlingStrategy,
)


def test_no_surrogates_returns_same_text():
    processor = EnhancedUnicodeProcessor()
    text = "Hello World"
    assert processor.process_text(text) == text


def test_replace_surrogates():
    cfg = SurrogateHandlingConfig(strategy=SurrogateHandlingStrategy.REPLACE)
    processor = EnhancedUnicodeProcessor(cfg)
    text = "A\ud800B"
    assert processor.process_text(text) == "A�B"


def test_strip_surrogates():
    cfg = SurrogateHandlingConfig(strategy=SurrogateHandlingStrategy.STRIP)
    processor = EnhancedUnicodeProcessor(cfg)
    text = "A\ud800B"
    assert processor.process_text(text) == "AB"


def test_reject_surrogates():
    cfg = SurrogateHandlingConfig(strategy=SurrogateHandlingStrategy.REJECT)
    processor = EnhancedUnicodeProcessor(cfg)
    with pytest.raises(UnicodeError):
        processor.process_text("A\ud800B")


def test_normalization_applied():
    processor = EnhancedUnicodeProcessor()
    text = "cafe\u0301"
    assert processor.process_text(text) == "café"
