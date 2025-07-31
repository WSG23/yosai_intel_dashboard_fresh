import sys
import types
import unicodedata
from pathlib import Path

# ensure repo root on path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# stub heavy dependencies required by imported modules
sys.modules.setdefault("redis", types.ModuleType("redis"))
sys.modules.setdefault("redis.asyncio", types.ModuleType("redis.asyncio"))
if "pydantic" not in sys.modules:
    pydantic_stub = types.ModuleType("pydantic")

    class BaseModel:
        pass

    def Field(*args, **kwargs):
        return None

    def model_validator(*args, **kwargs):
        def wrapper(fn):
            return fn

        return wrapper

    ConfigDict = dict
    pydantic_stub.BaseModel = BaseModel
    pydantic_stub.Field = Field
    pydantic_stub.model_validator = model_validator
    pydantic_stub.ConfigDict = ConfigDict
    sys.modules["pydantic"] = pydantic_stub

sys.modules.setdefault("google", types.ModuleType("google"))
if "google.protobuf" not in sys.modules:
    proto_pkg = types.ModuleType("google.protobuf")
    proto_pkg.json_format = types.ModuleType("google.protobuf.json_format")
    internal_mod = types.ModuleType("google.protobuf.internal")
    internal_mod.builder = object
    proto_pkg.internal = internal_mod
    sys.modules["google.protobuf"] = proto_pkg
    sys.modules["google.protobuf.json_format"] = proto_pkg.json_format
    sys.modules["google.protobuf.internal"] = internal_mod

# Load root test stubs for optional dependencies
import tests.conftest  # noqa: F401,E402

# Provide lightweight stubs for core and security modules used by UnicodeHandler
core_unicode = types.ModuleType("core.unicode")


def clean_surrogate_chars(text: str) -> str:
    return text.encode("utf-16", "surrogatepass").decode("utf-16", "ignore")


core_unicode.clean_surrogate_chars = clean_surrogate_chars
sys.modules["core.unicode"] = core_unicode

security_validator = types.ModuleType("security.unicode_security_validator")


class UnicodeSecurityValidator:
    def validate_and_sanitize(self, text: str) -> str:
        cleaned = "".join(ch for ch in text if ord(ch) < 0x10000)
        return unicodedata.normalize("NFC", cleaned)


security_validator.UnicodeSecurityValidator = UnicodeSecurityValidator
sys.modules["security.unicode_security_validator"] = security_validator

from yosai_intel_dashboard.src.infrastructure.config.unicode_handler import UnicodeHandler  # noqa: E402


def test_sanitize_removes_surrogates_and_normalizes():
    text = "\ufeff\u200bA\ud83d\ude00"
    assert UnicodeHandler.sanitize(text) == "A"


def test_validate_utf8():
    assert UnicodeHandler.validate_utf8(b"valid")
    assert not UnicodeHandler.validate_utf8(b"\xff\xff")


def test_repair_text_reports_issues():
    repaired, issues = UnicodeHandler.repair_text("\ufeffA\u200b\ud800")
    assert repaired == "A"
    assert {
        "surrogates_removed",
        "bom_removed",
        "zero_width_removed",
    }.issubset(set(issues))
