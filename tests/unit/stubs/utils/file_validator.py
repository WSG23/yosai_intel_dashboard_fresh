from yosai_intel_dashboard.src.core.unicode import safe_decode_bytes


def safe_decode_with_unicode_handling(data: bytes, enc: str):
    return safe_decode_bytes(data, enc)
