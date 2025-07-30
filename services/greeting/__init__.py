from unicode_toolkit import safe_encode_text


class GreetingService:
    """Simple greeting service."""

    def greet(self, name: str) -> str:
        return f"Hello, {safe_encode_text(name)}!"
