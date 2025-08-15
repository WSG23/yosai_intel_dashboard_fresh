"""Redis-backed CSV storage repository for session data"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis

from yosai_intel_dashboard.src.utils.io_helpers import write_json

logger = logging.getLogger(__name__)


class CSVStorageRepository:
    """Redis-backed storage repository for session data persistence"""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.storage_dir = self.path.parent / "session_storage"
        redis_url = os.getenv("SESSION_REDIS_URL", "redis://localhost:6379/0")
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self._ensure_storage_directory()

    def _ensure_storage_directory(self) -> None:
        """Ensure the storage directory exists"""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage directory ensured: {self.storage_dir}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {e}")

    def _session_key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def initialize(self) -> bool:
        """Ensure Redis connection and storage directory"""
        try:
            self._ensure_storage_directory()
            self.redis.ping()
            logger.info("Repository initialized with Redis backend")
            return True
        except Exception as e:
            logger.error(f"Repository initialization failed: {e}")
            return False

    def store_session_data(self, session_id: str, data: Dict[str, Any]) -> None:
        """Store session data in Redis"""
        data_with_meta = {
            **data,
            "last_updated": datetime.now().isoformat(),
            "session_id": session_id,
        }
        self.redis.set(self._session_key(session_id), json.dumps(data_with_meta))

    def get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis"""
        data = self.redis.get(self._session_key(session_id))
        if data:
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode session {session_id}: {e}")
        return None

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
        keys = self.redis.keys(self._session_key("*"))
        return [k.split(":", 1)[1] for k in keys]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session from Redis"""
        try:
            return bool(self.redis.delete(self._session_key(session_id)))
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def cleanup_old_sessions(self, max_age_days: int = 7) -> int:
        """Clean up old session keys"""
        cleaned = 0
        cutoff = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        try:
            for key in self.redis.keys(self._session_key("*")):
                data = self.redis.get(key)
                if not data:
                    continue
                try:
                    payload = json.loads(data)
                    last_updated = payload.get("last_updated")
                    if (
                        last_updated
                        and datetime.fromisoformat(last_updated).timestamp() < cutoff
                    ):
                        self.redis.delete(key)
                        cleaned += 1
                except Exception:
                    continue
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
