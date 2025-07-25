"""Backward compatibility wrapper for UploadOrchestrator."""

from .orchestrator import UploadOrchestrator

UploadProcessingService = UploadOrchestrator

__all__ = ["UploadProcessingService", "UploadOrchestrator"]
