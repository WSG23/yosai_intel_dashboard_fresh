"""Persist and recall device mappings between uploads."""

import hashlib
import json
import logging
from unicode_toolkit import safe_encode_text
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol, runtime_checkable

import pandas as pd

from yosai_intel_dashboard.src.services.learning.src.api.consolidated_service import get_learning_service
from yosai_intel_dashboard.src.services.protocols.device_learning import DeviceLearningServiceProtocol


@runtime_checkable
class DeviceServiceProtocol(Protocol):
    """Lightweight interface for device learning services."""

    def get_learned_mappings(
        self, df: pd.DataFrame, filename: str
    ) -> Dict[str, Dict]: ...

    def apply_learned_mappings_to_global_store(
        self, df: pd.DataFrame, filename: str
    ) -> bool: ...

    def get_user_device_mappings(self, filename: str) -> Dict[str, Any]: ...

    def save_user_device_mappings(
        self, df: pd.DataFrame, filename: str, user_mappings: Dict[str, Any]
    ) -> bool: ...


if TYPE_CHECKING:
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks

logger = logging.getLogger(__name__)


class DeviceLearningService(DeviceLearningServiceProtocol):
    """Persistent device mapping learning service"""

    def __init__(self):
        self.storage_dir = Path("data/device_learning")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.learned_mappings = {}
        self._load_all_learned_mappings()

    def _get_file_fingerprint(self, df: pd.DataFrame, filename: str) -> str:
        """Create unique fingerprint for file based on structure and content sample"""
        fingerprint_data = {
            "filename": filename.split(".")[0],
            "columns": sorted(df.columns.tolist()),
            "shape": df.shape,
            "sample_devices": (
                sorted(df[self._find_device_column(df)].dropna().unique()[:5].tolist())
                if self._find_device_column(df)
                else []
            ),
        }
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()[:12]

    def _find_device_column(self, df: pd.DataFrame) -> Optional[str]:
        """Find the device/door column in the dataframe"""
        device_columns = [
            col
            for col in df.columns
            if any(
                keyword in col.lower()
                for keyword in ["device", "door", "location", "area", "room"]
            )
        ]
        return device_columns[0] if device_columns else None

    def _load_all_learned_mappings(self):
        """Load all learned mappings from storage"""
        try:
            for mapping_file in self.storage_dir.glob("mapping_*.json"):
                try:
                    with open(
                        mapping_file,
                        "r",
                        encoding="utf-8",
                        errors="replace",
                    ) as f:
                        data = json.load(f)
                        if "device_mappings" not in data and "mappings" in data:
                            data["device_mappings"] = data.get("mappings", {})
                        fingerprint = mapping_file.stem.replace("mapping_", "")
                        self.learned_mappings[fingerprint] = data
                    logger.info(f"Loaded learned mapping: {fingerprint}")
                except Exception as e:
                    logger.warning(f"Failed to load mapping file {mapping_file}: {e}")
        except Exception as e:
            logger.error(f"Failed to load learned mappings: {e}")

    def _persist_learned_mappings(self):
        """Persist all learned mappings to disk"""
        try:
            for fingerprint, data in self.learned_mappings.items():
                mapping_file = self.storage_dir / f"mapping_{fingerprint}.json"
                with open(mapping_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to persist learned mappings: {e}")
            raise  # Re-raise the exception instead of swallowing it

    def save_device_mappings(
        self, df: pd.DataFrame, filename: str, device_mappings: Dict[str, Dict]
    ) -> str:
        """Persist device mappings with additional metadata."""
        try:
            fingerprint = self._get_file_fingerprint(df, filename)

            # Prepare learning data with human corrections flag
            learning_data = {
                "fingerprint": fingerprint,
                "filename": filename,
                "learned_at": datetime.now().isoformat(),
                "device_count": len(device_mappings),
                "mappings": device_mappings,
                "file_info": {
                    "columns": df.columns.tolist(),
                    "shape": df.shape,
                    "device_column": self._find_device_column(df),
                },
                "has_human_corrections": any(
                    mapping.get("manually_edited", False)
                    for mapping in device_mappings.values()
                ),
            }

            # Save to file immediately
            mapping_file = self.storage_dir / f"mapping_{fingerprint}.json"
            with open(mapping_file, "w", encoding="utf-8") as f:
                json.dump(learning_data, f, indent=2)

            # Update in-memory cache
            self.learned_mappings[fingerprint] = learning_data

            logger.info(
                "✅ Saved %s device mappings for %s",
                len(device_mappings),
                safe_encode_text(filename),
            )
            logger.info(f"📁 File: {mapping_file}")

            return fingerprint

        except Exception as e:
            logger.error(f"❌ Failed to save device mappings: {e}")
            raise

    def get_learned_mappings(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict]:
        """Retrieve learned mappings for a file."""
        fingerprint = self._get_file_fingerprint(df, filename)

        # Check if we have learned mappings for this file
        if fingerprint in self.learned_mappings:
            learned_data = self.learned_mappings[fingerprint]
            logger.info(
                "🔄 Loaded %s learned mappings for %s",
                len(learned_data.get("mappings", {})),
                safe_encode_text(filename),
            )
            return learned_data.get("mappings", {})

        logger.info(
            "No learned mappings found for %s (fingerprint: %s)",
            safe_encode_text(filename),
            fingerprint,
        )
        return {}

    def apply_learned_mappings_to_global_store(
        self, df: pd.DataFrame, filename: str
    ) -> bool:
        """Apply learned mappings to the global AI mappings store with validation."""

        # DETAILED DEBUG
        logger.info("🔍 DEBUG apply_learned_mappings_to_global_store called:")
        logger.info("🔍 DEBUG - filename: %s", safe_encode_text(filename))

        try:
            from yosai_intel_dashboard.src.services.ai_mapping_store import ai_mapping_store

            learned_mappings = self.get_learned_mappings(df, filename)
            logger.info(
                f"🔍 DEBUG - learned_mappings returned: {len(learned_mappings)} items"
            )

            if learned_mappings:
                logger.info(
                    f"🔍 DEBUG - Sample devices from learned_mappings: {list(learned_mappings.keys())[:3]}"  # noqa: E501
                )
                logger.info(
                    f"🔍 DEBUG - Sample mapping content: {list(learned_mappings.values())[0] if learned_mappings else 'None'}"  # noqa: E501
                )

                # Check store before clearing
                store_before = ai_mapping_store.all()
                logger.info(
                    f"🔍 DEBUG - Store BEFORE clear: {len(store_before)} items"  # noqa: E501
                )

                # Clear existing AI mappings
                ai_mapping_store.clear()

                # Check store after clearing
                store_after_clear = ai_mapping_store.all()
                logger.info(
                    f"🔍 DEBUG - Store AFTER clear: {len(store_after_clear)} items"  # noqa: E501
                )

                # Apply learned mappings
                ai_mapping_store.update(learned_mappings)

                # Check store after update
                store_after_update = ai_mapping_store.all()
                logger.info(
                    f"🔍 DEBUG - Store AFTER update: {len(store_after_update)} items"  # noqa: E501
                )
                logger.info(
                    f"🔍 DEBUG - Store keys after update: {list(store_after_update.keys())[:3]}"  # noqa: E501
                )

                logger.info(
                    f"🤖 Applied {len(learned_mappings)} learned mappings to AI store"  # noqa: E501
                )
                return True
            else:
                logger.info("🔍 DEBUG - No learned mappings found to apply")

            return False

        except Exception as e:
            logger.error(f"Error applying learned mappings to global store: {e}")
            import traceback

            logger.error(f"Full error details: {traceback.format_exc()}")
            return False

    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of all learned mappings"""
        return {
            "total_learned_files": len(self.learned_mappings),
            "files": [
                {
                    "filename": data["filename"],
                    "learned_at": data["learned_at"],
                    "device_count": data["device_count"],
                }
                for data in self.learned_mappings.values()
            ],
        }

    def save_user_device_mappings(
        self, df: pd.DataFrame, filename: str, user_mappings: Dict[str, Any]
    ) -> bool:
        """Save user-confirmed device mappings to database"""
        logger.info("🔍 DEBUG save_user_device_mappings called:")
        logger.info("🔍 DEBUG - filename: %s", safe_encode_text(filename))
        logger.info(f"🔍 DEBUG - user_mappings type: {type(user_mappings)}")
        logger.info(
            f"🔍 DEBUG - user_mappings length: {len(user_mappings) if user_mappings else 'None'}"  # noqa: E501
        )
        if user_mappings:
            logger.info(
                f"🔍 DEBUG - first 3 devices: {list(user_mappings.keys())[:3]}"  # noqa: E501
            )
            logger.info(
                f"🔍 DEBUG - sample mapping: {list(user_mappings.values())[0] if user_mappings else 'None'}"  # noqa: E501
            )
        else:
            logger.info("🔍 DEBUG - user_mappings is empty or None!")

        try:
            fingerprint = self._get_file_fingerprint(df, filename)

            mapping_data = {
                "filename": filename,
                "fingerprint": fingerprint,
                "saved_at": datetime.now().isoformat(),
                "device_mappings": user_mappings,
                "source": "user_confirmed",
                "device_count": len(user_mappings),
            }

            self.learned_mappings[fingerprint] = mapping_data
            # This will now raise exception if it fails
            self._persist_learned_mappings()

            logger.info(
                "✅ Saved user device mappings for %s: %s devices",
                safe_encode_text(filename),
                len(user_mappings),
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save user device mappings: {e}")
            # Also log the actual exception details
            import traceback

            logger.error(f"Full error details: {traceback.format_exc()}")
            return False

    def get_user_device_mappings(self, filename: str) -> Dict[str, Any]:
        """Get user-confirmed device mappings for a filename"""
        try:
            for fingerprint, data in self.learned_mappings.items():
                if (
                    data.get("filename") == filename
                    and data.get("source") == "user_confirmed"
                ):
                    return data.get("device_mappings") or data.get("mappings", {})

            logger.info(
                "No user device mappings found for %s",
                safe_encode_text(filename),
            )
            return {}

        except Exception as e:
            logger.error(f"Error getting user device mappings: {e}")
            return {}

    def get_device_mapping_by_name(self, device_name: str) -> Dict[str, Any]:
        """Get consistent mapping for a device name across all learned files"""
        try:
            for fingerprint, data in self.learned_mappings.items():
                mappings = data.get("device_mappings", {})
                if device_name in mappings:
                    device_mapping = mappings[device_name].copy()
                    device_mapping["source_file"] = data.get("filename")
                    device_mapping["confidence"] = 1.0
                    return device_mapping

            for fingerprint, data in self.learned_mappings.items():
                mappings = data.get("device_mappings", {})
                for stored_name, stored_mapping in mappings.items():
                    if self._device_names_similar(device_name, stored_name):
                        similar_mapping = stored_mapping.copy()
                        similar_mapping["source_file"] = data.get("filename")
                        similar_mapping["confidence"] = 0.8
                        return similar_mapping

            return {}

        except Exception as e:
            logger.error(f"Error getting device mapping by name: {e}")
            return {}

    def _device_names_similar(self, name1: str, name2: str) -> bool:
        """Check if two device names are similar enough to share mappings"""
        clean1 = name1.lower().replace("_", " ").replace("-", " ")
        clean2 = name2.lower().replace("_", " ").replace("-", " ")

        words1 = set(clean1.split())
        words2 = set(clean2.split())

        if not words1 or not words2:
            return False

        overlap = len(words1 & words2)
        total = len(words1 | words2)

        return overlap / total >= 0.6


def create_device_learning_service() -> DeviceLearningService:
    """Factory function for :class:`DeviceLearningService`."""
    return DeviceLearningService()


