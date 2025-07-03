class Container:
    """Registry for application services used to resolve dependencies."""

    def __init__(self):
        # Stores registered services keyed by name
        self._services = {}

    def register(self, name: str, service):
        """Register a service instance under the given ``name``."""
        self._services[name] = service

    def get(self, name: str):
        """Retrieve a previously registered service by name."""
        return self._services.get(name)

    def has(self, name: str) -> bool:
        """Check if a service with the given name exists."""
        return name in self._services
