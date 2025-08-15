from yosai_intel_dashboard.src.core.callback_modules import CallbackModuleRegistry


class DummyModule:
    COMPONENT_ID = "mod"
    NAMESPACE = "test"

    def __init__(self, callback_ids):
        self.callback_ids = list(callback_ids)
        self.initialized_with = None

    def register_callbacks(self, manager):
        self.initialized_with = manager

    def get_callback_ids(self):
        return self.callback_ids


def test_module_registration():
    registry = CallbackModuleRegistry()
    module = DummyModule(["a", "b"])
    assert registry.register_module(module)
    assert registry.get_module("mod") is module


def test_duplicate_component_id():
    registry = CallbackModuleRegistry()
    first = DummyModule(["a"])
    second = DummyModule(["b"])
    second.COMPONENT_ID = first.COMPONENT_ID

    assert registry.register_module(first)
    assert not registry.register_module(second)
    assert registry.get_module(first.COMPONENT_ID) is first


def test_callback_id_conflict():
    registry = CallbackModuleRegistry()
    mod1 = DummyModule(["a", "b"])
    mod1.COMPONENT_ID = "m1"
    mod2 = DummyModule(["b", "c"])
    mod2.COMPONENT_ID = "m2"

    assert registry.register_module(mod1)
    assert not registry.register_module(mod2)
    assert registry.get_module("m2") is None


def test_initialize_all_calls_register():
    registry = CallbackModuleRegistry()
    module = DummyModule(["x"])
    registry.register_module(module)

    manager = object()
    registry.initialize_all(manager)

    assert module.initialized_with is manager
