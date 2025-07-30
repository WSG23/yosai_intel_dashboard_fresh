import importlib
import types
import sys


def test_greeting_service_uses_safe_encode():
    fake = types.ModuleType("unicode_toolkit")
    captured = {}

    def sanitize(val):
        captured['val'] = val
        return 'clean'

    fake.safe_encode_text = sanitize
    sys.modules['unicode_toolkit'] = fake
    import services.greeting as greeting
    importlib.reload(greeting)

    svc = greeting.GreetingService()
    assert svc.greet('<bad>') == 'Hello, clean!'
    assert captured['val'] == '<bad>'
