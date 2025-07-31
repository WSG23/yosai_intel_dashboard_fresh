import pytest

from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer


class Foo:
    pass


class Bar:
    def __init__(self, foo: Foo):
        self.foo = foo


class WithForwardRef:
    def __init__(self, other: "Bar"):
        self.other = other


class Unresolved:
    def __init__(self, missing: "MissingType"):
        self.missing = missing


def test_dependencies_resolved_using_type_hints():
    c = ServiceContainer()
    c.register_singleton("foo", Foo)
    c.register_transient("bar", Bar)
    c.register_transient("fw", WithForwardRef)
    reg_bar = c._services["bar"]
    reg_fw = c._services["fw"]
    assert reg_bar.dependencies == [("foo", Foo)]
    assert reg_fw.dependencies == [("other", Bar)]


def test_unresolved_annotation_keeps_string():
    c = ServiceContainer()
    # Should not raise when registering
    c.register_transient("un", Unresolved)
    reg = c._services["un"]
    assert reg.dependencies == [("missing", "MissingType")]
