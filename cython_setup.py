from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize(
        "yosai_intel_dashboard/src/core/_fast_unicode.pyx",
        language_level=3,
    )
)
