#!/usr/bin/env python3
"""Generate configuration reference documentation from Pydantic models."""
from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Type
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config"
sys.path.insert(0, str(CONFIG_PATH))

from pydantic import BaseModel
from pydantic.fields import PydanticUndefined

import importlib.util
import types

spec = importlib.util.spec_from_file_location("config.pydantic_models", CONFIG_PATH / "pydantic_models.py")
pyd_models = importlib.util.module_from_spec(spec)
assert spec.loader
sys.modules.setdefault("config", types.ModuleType("config"))
sys.modules["config"].__path__ = [str(CONFIG_PATH)]
spec.loader.exec_module(pyd_models)

AppModel = pyd_models.AppModel
DatabaseModel = pyd_models.DatabaseModel
SecurityModel = pyd_models.SecurityModel
SampleFilesModel = pyd_models.SampleFilesModel
AnalyticsModel = pyd_models.AnalyticsModel
MonitoringModel = pyd_models.MonitoringModel
CacheModel = pyd_models.CacheModel
UploadModel = pyd_models.UploadModel
SecretValidationModel = pyd_models.SecretValidationModel


def make_table(model: Type[BaseModel]) -> str:
    """Return a markdown table for a Pydantic model."""
    header = "| Field | Default | Env Var |\n|-------|--------|--------|"
    lines: List[str] = [header]
    for name, field in model.model_fields.items():
        default = field.default
        if default is PydanticUndefined and field.default_factory is not None:
            try:
                default = field.default_factory()
            except Exception:
                default = "<factory>"
        env = ""
        if field.json_schema_extra and "env" in field.json_schema_extra:
            env = field.json_schema_extra["env"]
        lines.append(f"| `{name}` | `{default}` | `{env}` |")
    return "\n".join(lines) + "\n"


def generate() -> str:
    sections: List[Tuple[str, Type[BaseModel]]] = [
        ("App", AppModel),
        ("Database", DatabaseModel),
        ("Security", SecurityModel),
        ("Sample Files", SampleFilesModel),
        ("Analytics", AnalyticsModel),
        ("Monitoring", MonitoringModel),
        ("Cache", CacheModel),
        ("Uploads", UploadModel),
        ("Secret Validation", SecretValidationModel),
    ]
    parts = ["# Configuration Reference\n"]
    for title, model in sections:
        parts.append(f"## {title}\n")
        parts.append(make_table(model))
    return "\n".join(parts)


def main() -> None:
    out_file = Path("docs/configuration_reference.md")
    out_file.write_text(generate())
    print(f"Wrote {out_file}")


if __name__ == "__main__":
    main()
