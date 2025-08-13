import pathlib
import py_compile


def test_locust_scripts_compile():
    locust_dir = pathlib.Path(__file__).parent / "locust"
    for path in locust_dir.glob("*.py"):
        if path.name == "__init__.py":
            continue
        py_compile.compile(str(path), doraise=True)
