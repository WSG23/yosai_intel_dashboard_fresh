from __future__ import annotations

import pytest


@pytest.mark.memlimit(200)
def test_process_memory_cap():
    with pytest.raises(MemoryError):
        _ = bytearray(300 * 1024 * 1024)
