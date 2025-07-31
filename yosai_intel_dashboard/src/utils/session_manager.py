"""Session management utilities for persistent data"""

import logging
from typing import Any, Dict, List, Optional

from yosai_intel_dashboard.src.components.plugin_adapter import ComponentPluginAdapter

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage session data persistence and retrieval"""

    def __init__(self):
        self.adapter = ComponentPluginAdapter()
        self.ai_plugin = None
        self._initialize_plugin()

    def _initialize_plugin(self):
        """Initialize AI plugin for data access"""
        try:
            self.ai_plugin = self.adapter.get_ai_plugin()
        except Exception as e:
            logger.error(f"Failed to initialize AI plugin: {e}")

    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get all data for a session"""
        if not self.ai_plugin:
            return None
        try:
            return self.ai_plugin.get_session_data(session_id)
        except Exception as e:
            logger.error(f"Failed to get session data: {e}")
            return None

    def get_processed_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get processed CSV data for a session"""
        if not self.ai_plugin or not self.ai_plugin.csv_repository:
            return None
        try:
            return self.ai_plugin.csv_repository.get_processed_data(session_id)
        except Exception as e:
            logger.error(f"Failed to get processed data: {e}")
            return None

    def list_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent sessions with metadata"""
        if not self.ai_plugin or not self.ai_plugin.csv_repository:
            return []
        try:
            session_ids = self.ai_plugin.csv_repository.list_sessions()
            sessions = []
            for session_id in session_ids[-limit:]:
                session_data = self.get_session_data(session_id)
                if session_data:
                    processed_data = session_data.get("processed_data", {})
                    sessions.append(
                        {
                            "session_id": session_id,
                            "filename": processed_data.get("filename", "Unknown"),
                            "upload_time": processed_data.get("upload_timestamp", ""),
                            "row_count": processed_data.get("row_count", 0),
                            "headers": processed_data.get("headers", []),
                        }
                    )
            return sorted(sessions, key=lambda x: x["upload_time"], reverse=True)
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    def cleanup_old_sessions(self, max_age_days: int = 7) -> int:
        """Clean up old session data"""
        if not self.ai_plugin or not self.ai_plugin.csv_repository:
            return 0
        try:
            return self.ai_plugin.csv_repository.cleanup_old_sessions(max_age_days)
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")
            return 0


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager(manager: Optional[SessionManager] = None) -> SessionManager:
    """Return a global session manager instance.

    If ``manager`` is provided, it becomes the global instance. Otherwise an
    instance is created on first access.
    """
    global _session_manager
    if manager is not None:
        _session_manager = manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def create_session_manager() -> SessionManager:
    """Create a new session manager instance."""
    return SessionManager()


__all__ = [
    "SessionManager",
    "get_session_manager",
    "create_session_manager",
]
