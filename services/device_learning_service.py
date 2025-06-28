import json
import hashlib
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import pandas as pd
from dash import html
from dash._callback import callback
from dash.dependencies import Input, Output
from services.consolidated_learning_service import get_learning_service
from dash._callback_context import callback_context

logger = logging.getLogger(__name__)


class DeviceLearningService:
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
                    with open(mapping_file, "r") as f:
                        data = json.load(f)
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
                with open(mapping_file, "w") as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist learned mappings: {e}")

    def save_device_mappings(
        self, df: pd.DataFrame, filename: str, device_mappings: Dict[str, Dict]
    ) -> str:
        """Save device mappings with enhanced persistence - FIXED"""
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
            with open(mapping_file, "w") as f:
                json.dump(learning_data, f, indent=2)

            # Update in-memory cache
            self.learned_mappings[fingerprint] = learning_data

            logger.info(
                f"✅ Saved {len(device_mappings)} device mappings for {filename}"
            )
            logger.info(f"📁 File: {mapping_file}")

            return fingerprint

        except Exception as e:
            logger.error(f"❌ Failed to save device mappings: {e}")
            raise

    def get_learned_mappings(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict]:
        """Get learned mappings for a file - FIXED to actually return learned data"""
        fingerprint = self._get_file_fingerprint(df, filename)

        # Check if we have learned mappings for this file
        if fingerprint in self.learned_mappings:
            learned_data = self.learned_mappings[fingerprint]
            logger.info(
                f"🔄 Loaded {len(learned_data.get('mappings', {}))} learned mappings for {filename}"
            )
            return learned_data.get("mappings", {})

        logger.info(
            f"No learned mappings found for {filename} (fingerprint: {fingerprint})"
        )
        return {}

    def apply_learned_mappings_to_global_store(self, df: pd.DataFrame, filename: str):
        """Apply learned mappings to the global AI mappings store - NEW METHOD"""
        from components.simple_device_mapping import _device_ai_mappings

        learned_mappings = self.get_learned_mappings(df, filename)

        if learned_mappings:
            # Clear existing AI mappings
            _device_ai_mappings.clear()

            # Apply learned mappings
            _device_ai_mappings.update(learned_mappings)

            logger.info(
                f"🤖 Applied {len(learned_mappings)} learned mappings to AI store"
            )
            return True

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

    def save_user_device_mappings(self, filename: str, user_mappings: Dict[str, Any]) -> bool:
        """Save user-confirmed device mappings to database"""
        try:
            fingerprint = f"user_devices_{filename}_{len(user_mappings)}"

            mapping_data = {
                "filename": filename,
                "fingerprint": fingerprint,
                "saved_at": datetime.now().isoformat(),
                "device_mappings": user_mappings,
                "source": "user_confirmed",
                "device_count": len(user_mappings),
            }

            self.learned_mappings[fingerprint] = mapping_data
            self._persist_learned_mappings()

            logger.info(
                f"✅ Saved user device mappings for {filename}: {len(user_mappings)} devices"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Failed to save user device mappings: {e}")
            return False

    def get_user_device_mappings(self, filename: str) -> Dict[str, Any]:
        """Get user-confirmed device mappings for a filename"""
        try:
            for fingerprint, data in self.learned_mappings.items():
                if data.get("filename") == filename and data.get("source") == "user_confirmed":
                    return data.get("device_mappings", {})

            logger.info(f"No user device mappings found for {filename}")
            return {}

        except Exception as e:
            logger.error(f"Error getting user device mappings: {e}")
            return {}


_device_learning_service = DeviceLearningService()


def get_device_learning_service() -> DeviceLearningService:
    return _device_learning_service


def create_learning_callbacks():
    """Updated callback using consolidated learning service."""

    @callback(
        Output("device-learning-status", "children"),
        [
            Input("file-upload-store", "data"),
            Input("device-mappings-confirmed", "data"),
        ],
        prevent_initial_call=True,
    )
    def handle_device_learning(upload_data, confirmed_mappings):
        """Handle learning using consolidated service."""
        ctx = callback_context

        if not ctx.triggered:
            return ""

        trigger_id = ctx.triggered[0]["prop_id"]

        learning_service = get_learning_service()

        if "file-upload-store" in trigger_id and upload_data:
            # File uploaded - try to apply learned mappings
            df = pd.DataFrame(upload_data["data"])
            filename = upload_data["filename"]

            if learning_service.apply_to_global_store(df, filename):
                return html.Div(
                    [
                        html.I(className="fas fa-brain me-2"),
                        "Learned device mappings applied!",
                    ],
                    className="text-success",
                )

        elif "device-mappings-confirmed" in trigger_id and confirmed_mappings:
            # Mappings confirmed - save for future use
            df = pd.DataFrame(confirmed_mappings["original_data"])
            filename = confirmed_mappings["filename"]
            mappings = confirmed_mappings["mappings"]

            fingerprint = learning_service.save_complete_mapping(df, filename, mappings)

            return html.Div(
                [
                    html.I(className="fas fa-save me-2"),
                    f"Mappings saved! ID: {fingerprint[:8]}",
                ],
                className="text-success",
            )

        return ""
