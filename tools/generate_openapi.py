from pathlib import Path
import json
import sys

try:
    from flasgger import Swagger
except ImportError as exc:
    print(
        "Flasgger is required to generate the OpenAPI specification.\n"
        "Install it with 'pip install flasgger'."
    )
    sys.exit(1)

from core.app_factory import create_app


def main() -> None:
    app = create_app()
    server = app.server
    swagger = Swagger(server, template={"openapi": "3.0.2"})
    with server.app_context():
        spec = (
            swagger.get_apispecs()[0].to_dict()
            if hasattr(swagger, "get_apispecs")
            else swagger.template
        )
        Path("docs").mkdir(exist_ok=True)
        with open(Path("docs") / "openapi.json", "w") as fh:
            json.dump(spec, fh, indent=2)


if __name__ == "__main__":
    main()
