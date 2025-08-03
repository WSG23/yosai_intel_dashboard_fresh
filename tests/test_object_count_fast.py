import importlib.util
import pathlib
import pytest

core_dir = pathlib.Path('yosai_intel_dashboard/src/core')
so_files = list(core_dir.glob('_fast_unicode*.so'))
if not so_files:
    pytest.skip('Cython extension not built', allow_module_level=True)

spec = importlib.util.spec_from_file_location('_fast_unicode', so_files[0])
_fast = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_fast)


def object_count_py(items):
    counts = {}
    for item in items:
        if isinstance(item, str):
            counts[item] = counts.get(item, 0) + 1
    return sum(1 for v in counts.values() if v > 1)


def test_object_count_fast_matches_python():
    data = ['a', 'b', 'a', 'c', 'b', 'b', 1, None]
    assert _fast.object_count_fast(data) == object_count_py(data)
