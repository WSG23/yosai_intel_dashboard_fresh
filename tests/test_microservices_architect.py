import importlib.util
import pathlib
import sys

spec = importlib.util.spec_from_file_location(
    "microservices_architect",
    pathlib.Path(__file__).resolve().parents[1]
    / "services"
    / "microservices_architect.py",
)
microservices_architect = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = microservices_architect
spec.loader.exec_module(microservices_architect)
MicroservicesArchitect = microservices_architect.MicroservicesArchitect


def test_generate_microservices_roadmap():
    modules = {"analytics": object(), "utils": object()}
    architect = MicroservicesArchitect(modules)
    roadmap = architect.generate_microservices_roadmap()

    assert set(roadmap.keys()) == {"boundaries", "phases"}
    assert len(roadmap["boundaries"]) == 2
    names = {b["name"] for b in roadmap["boundaries"]}
    assert {"Analytics Service", "Core Service"} == names
    assert roadmap["phases"][0]["name"] == "Assessment"
