# Service Discovery

The platform uses a lightweight Consul based discovery mechanism so that
services can locate each other without hard coded addresses.  Each service
queries Consul's HTTP API at startup to resolve the host and port for its
dependencies.

## Configuration

Set the location of your Consul agent using environment variables:

```
CONSUL_HOST=consul.service
CONSUL_PORT=8500
```

When a service needs to contact another service it asks the discovery helper
for the endpoint:

```python
from yosai_intel_dashboard.src.services.common.service_discovery import (
    ConsulServiceDiscovery,
)

sd = ConsulServiceDiscovery()
address = sd.get_service("analytics-db")
```

The helper returns a ``host:port`` string or ``None`` if the service is not
registered.  In the analytics microservice the resolved database address is used
on startup to populate ``DATABASE_URL`` when available.

## Environment Overlays

Configuration files now live in ``config/environments`` with one overlay per
environment (``development.yaml``, ``staging.yaml``, ``production.yaml`` and
``test.yaml``).  ``config/environment.py`` selects the appropriate overlay based
on ``YOSAI_ENV`` or the ``YOSAI_CONFIG_FILE`` variable.
