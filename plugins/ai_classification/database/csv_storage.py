"""File-based CSV storage repository with persistence"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.io_helpers import read_json, write_json
from utils.unicode_handler import UnicodeHandler

logger = logging.getLogger(__name__)


class CSVStorageRepository:
    """File-based storage repository for session data persistence"""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.storage_dir = self.path.parent / "session_storage"
        self.sessions: Dict[str, Any] = {}  # In-memory cache
        self._ensure_storage_directory()

    def _ensure_storage_directory(self) -> None:
        """Ensure the storage directory exists"""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage directory ensured: {self.storage_dir}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {e}")

    def _get_session_file_path(self, session_id: str) -> Path:
        """Get the file path for a session"""
        return self.storage_dir / f"session_{session_id}.json"

    def _load_session_from_file(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from file"""
        try:
            file_path = self._get_session_file_path(session_id)
            if file_path.exists():
                data = read_json(file_path)
                self.sessions[session_id] = data
                logger.info("Sanitized read from %s", file_path)
                return data
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
        return None

    def _save_session_to_file(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Save session data to file"""
        try:
            file_path = self._get_session_file_path(session_id)

            data_with_meta = {
                **data,
                "last_updated": datetime.now().isoformat(),
                "session_id": session_id,
            }

            write_json(file_path, data_with_meta)
            logger.info("Sanitized write to %s", file_path)

            self.sessions[session_id] = data_with_meta
            logger.info(f"Session {session_id} saved to file")
            return True
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            return False

    def initialize(self) -> bool:
        """Initialize the repository and load existing sessions"""
        try:
            self._ensure_storage_directory()

            if self.storage_dir.exists():
                for file_path in self.storage_dir.glob("session_*.json"):
                    try:
                        session_id = file_path.stem.replace("session_", "")
                        self._load_session_from_file(session_id)
                    except Exception as e:
                        logger.warning(f"Failed to load session file {file_path}: {e}")

            logger.info(f"Repository initialized with {len(self.sessions)} sessions")
            return True
        except Exception as e:
            logger.error(f"Repository initialization failed: {e}")
            return False

    def store_session_data(self, session_id: str, data: Dict[str, Any]) -> None:
        """Store session data with file persistence"""
        self.sessions[session_id] = data
        self._save_session_to_file(session_id, data)

    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from memory or file"""
        if session_id in self.sessions:
            return self.sessions[session_id]
        return self._load_session_from_file(session_id)

    def update_session_data(self, session_id: str, updates: Dict[str, Any]) -> None:
        """Update existing session data"""
        current_data = self.get_session_data(session_id) or {}
        current_data.update(updates)
        self.store_session_data(session_id, current_data)

    # Column mapping
    def store_column_mapping(self, session_id: str, mapping: Dict[str, Any]) -> None:
        """Store column mapping data"""
        self.update_session_data(session_id, {"column_mapping": mapping})

    def update_column_mapping(self, session_id: str, mapping: Dict[str, Any]) -> None:
        """Update column mapping data"""
        self.store_column_mapping(session_id, mapping)

    def get_column_mapping(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get column mapping data"""
        sess = self.get_session_data(session_id)
        if sess:
            return sess.get("column_mapping")
        return None

    # Floor estimation
    def store_floor_estimation(self, session_id: str, data: Dict[str, Any]) -> None:
        """Store floor estimation data"""
        self.update_session_data(session_id, {"floor_estimation": data})

    def get_floor_estimation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get floor estimation data"""
        sess = self.get_session_data(session_id)
        if sess:
            return sess.get("floor_estimation")
        return None

    # Entry classification
    def store_entry_classification(self, session_id: str, data: Any) -> None:
        """Store entry classification data"""
        self.update_session_data(session_id, {"entry_classification": data})

    def get_entry_classification(self, session_id: str) -> Optional[Any]:
        """Get entry classification data"""
        sess = self.get_session_data(session_id)
        if sess:
            return sess.get("entry_classification")
        return None

    # Processed data storage
    def store_processed_data(self, session_id: str, data: Dict[str, Any]) -> None:
        """Store cleaned and processed CSV data"""
        self.update_session_data(session_id, {"processed_data": data})

    def get_processed_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get processed CSV data"""
        sess = self.get_session_data(session_id)
        if sess:
            return sess.get("processed_data")
        return None

    # Session management
    def list_sessions(self) -> List[str]:
        """List all available session IDs"""
        return list(self.sessions.keys())

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its file"""
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]

            file_path = self._get_session_file_path(session_id)
            if file_path.exists():
                file_path.unlink()

            logger.info(f"Session {session_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def cleanup_old_sessions(self, max_age_days: int = 7) -> int:
        """Clean up old session files"""
        cleaned = 0
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)

            for file_path in self.storage_dir.glob("session_*.json"):
                if file_path.stat().st_mtime < cutoff_time:
                    session_id = file_path.stem.replace("session_", "")
                    if self.delete_session(session_id):
                        cleaned += 1

            logger.info(f"Cleaned up {cleaned} old sessions")
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")

        return cleaned

    # Permanent storage
    def save_permanent_data(self, session_id: str, client_id: str) -> bool:
        """Save session data permanently with client association"""
        try:
            session_data = self.get_session_data(session_id)
            if not session_data:
                return False

            permanent_dir = self.storage_dir / "permanent" / client_id
            permanent_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            permanent_file = permanent_dir / f"data_{timestamp}.json"

            permanent_data = {
                **session_data,
                "client_id": client_id,
                "original_session_id": session_id,
                "saved_at": datetime.now().isoformat(),
            }

            write_json(permanent_file, permanent_data)
            logger.info("Sanitized write to %s", permanent_file)

            logger.info(
                f"Session {session_id} saved permanently for client {client_id}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save permanent data: {e}")
            return False
