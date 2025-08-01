"""Storage-related interfaces."""

from .protocols import FileStorageProtocol, DatabaseStorageProtocol

__all__ = [
    "FileStorageProtocol",
    "DatabaseStorageProtocol",
]
