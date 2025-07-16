import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "api_gateway_planner",
    Path(__file__).resolve().parents[2] / "services" / "api_gateway_planner.py",
)
api_gateway_planner = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(api_gateway_planner)
APIGatewayArchitect = api_gateway_planner.APIGatewayArchitect


def test_design_api_gateway_keys():
    architect = APIGatewayArchitect()
    boundaries = {"users": ["/users", "/users/{id}"], "orders": ["/orders"]}
    plan = architect.design_api_gateway(boundaries)

    assert set(plan.keys()) == {"routing", "security", "observability"}
    assert "rules" in plan["routing"]
    assert "policies" in plan["security"]
    assert "hooks" in plan["observability"]


def test_design_service_mesh_keys():
    architect = APIGatewayArchitect()
    mesh = architect.design_service_mesh(["users", "orders"])

    assert set(mesh.keys()) == {"service_entries", "traffic_policies", "observability"}
