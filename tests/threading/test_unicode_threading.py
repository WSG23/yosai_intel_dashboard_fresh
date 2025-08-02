import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from yosai_intel_dashboard.src.core.unicode import ChunkedUnicodeProcessor, UnicodeProcessor


def test_clean_surrogate_chars_threaded():
    pattern = "Hello" + chr(0xD800) + "World" + chr(0xDC00)
    text = pattern * 100000  # >1MB

    expected = UnicodeProcessor.clean_surrogate_chars(text)

    def worker(_: int) -> str:
        return UnicodeProcessor.clean_surrogate_chars(text)

    with ThreadPoolExecutor(max_workers=5) as exc:
        results = list(exc.map(worker, range(10)))

    for result in results:
        assert result == expected


def test_process_large_content_threaded():
    pattern = "Test" + chr(0xD83D) + chr(0xDE00) + "Content"
    content = (pattern * 100000).encode("utf-8", "surrogatepass")  # >1MB
    chunk_size = 50 * 1024

    expected = ChunkedUnicodeProcessor.process_large_content(
        content, chunk_size=chunk_size
    )

    def worker(_: int) -> str:
        return ChunkedUnicodeProcessor.process_large_content(
            content, chunk_size=chunk_size
        )

    with ThreadPoolExecutor(max_workers=5) as exc:
        results = list(exc.map(worker, range(10)))

    for result in results:
        assert result == expected
