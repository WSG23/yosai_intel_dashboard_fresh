# cython: language_level=3
from cpython.unicode cimport PyUnicode_Check

def object_count_fast(object items):
    """Cython-accelerated version of :func:`object_count`."""
    cdef dict counts = {}
    cdef object item
    for item in items:
        if PyUnicode_Check(item):
            counts[item] = counts.get(item, 0) + 1
    cdef Py_ssize_t total = 0
    cdef int v
    for v in counts.values():
        if v > 1:
            total += 1
    return total
