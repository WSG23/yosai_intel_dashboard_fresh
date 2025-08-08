"""Integration helpers for external threat intelligence systems.

Heavy dependencies (such as ``networkx``) are only required when STIX/TAXII
exports are used.
"""

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = ["export_to_stix", "push_to_taxii", "send_to_siem"]

_LAZY_EXPORTS = {
    "export_to_stix": (".stix_taxii_exporter", "export_to_stix"),
    "push_to_taxii": (".stix_taxii_exporter", "push_to_taxii"),
    "send_to_siem": (".siem_connectors", "send_to_siem"),
}

if TYPE_CHECKING:  # pragma: no cover - imported for type checkers only
    from .siem_connectors import send_to_siem
    from .stix_taxii_exporter import export_to_stix, push_to_taxii


def __getattr__(name: str) -> Any:
    """Load integration helpers lazily."""

    if name in _LAZY_EXPORTS:
        module_name, attr_name = _LAZY_EXPORTS[name]
        module = import_module(module_name, __name__)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(name)
