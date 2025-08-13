from A import A
from B import B, create_a


def test_import_and_usage() -> None:
    """Modules should import without circular dependencies."""

    b = B()
    a = A(b)
    assert a.do_a() == "A -> B"

    a2 = create_a()
    assert a2.do_a() == "A -> B"
