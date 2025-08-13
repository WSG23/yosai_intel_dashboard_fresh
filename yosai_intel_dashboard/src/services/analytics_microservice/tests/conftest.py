import importlib.util
import os
import pathlib
import sys
import types
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from jose import jwt

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2]

# Stub out the heavy 'services' package before tests import anything
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_stub)

# Stub hierarchical packages to prevent loading the full application
yosai_stub = types.ModuleType("yosai_intel_dashboard")
src_stub = types.ModuleType("yosai_intel_dashboard.src")
services_pkg_stub = types.ModuleType("yosai_intel_dashboard.src.services")
services_pkg_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("yosai_intel_dashboard", yosai_stub)
sys.modules.setdefault("yosai_intel_dashboard.src", src_stub)
sys.modules.setdefault("yosai_intel_dashboard.src.services", services_pkg_stub)
