import logging
from typing import Any, Dict, List, Tuple

import pandas as pd
from dash import html
from dash.dash import no_update
import dash_bootstrap_components as dbc

from services.data_processing import process_file


def create_file_preview(df: pd.DataFrame, filename: str) -> dbc.Card:
    """Return a very small preview card for the uploaded file."""
    return dbc.Card([
        dbc.CardHeader(html.H6(filename)),
        dbc.CardBody(
            [
                html.Small(f"{len(df):,} rows × {len(df.columns)} cols"),
            ]
        ),
    ])
from services.device_learning_service import get_device_learning_service
from services.data_enhancer import get_ai_column_suggestions
from utils.upload_store import UploadedDataStore

logger = logging.getLogger(__name__)


class UploadProcessingService:
    """Service handling processing of uploaded files."""

    def __init__(self, store: UploadedDataStore):
        self.store = store

    def build_success_alert(
        self,
        filename: str,
        rows: int,
        cols: int,
        prefix: str = "Successfully uploaded",
        processed: bool = True,
    ) -> dbc.Alert:
        details = f"📊 {rows:,} rows × {cols} columns"
        if processed:
            details += " processed"
        timestamp = pd.Timestamp.now().strftime("%H:%M:%S")
        return dbc.Alert(
            [
                html.H6(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        f"{prefix} {filename}",
                    ],
                    className="alert-heading",
                ),
                html.P(
                    [
                        details,
                        html.Br(),
                        html.Small(f"Processed at {timestamp}", className="text-muted"),
                    ]
                ),
            ],
            color="success",
            className="mb-3",
        )

    def build_failure_alert(self, message: str) -> dbc.Alert:
        return dbc.Alert(
            [html.H6("Upload Failed", className="alert-heading"), html.P(message)],
            color="danger",
        )

    def auto_apply_learned_mappings(self, df: pd.DataFrame, filename: str) -> bool:
        try:
            learning_service = get_device_learning_service()
            learned = learning_service.get_learned_mappings(df, filename)
            if learned:
                learning_service.apply_learned_mappings_to_global_store(df, filename)
                logger.info("🤖 Auto-applied %s learned device mappings", len(learned))
                return True
            return False
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Failed to auto-apply learned mappings: %s", exc)
            return False

    def build_file_preview_component(self, df: pd.DataFrame, filename: str) -> html.Div:
        return html.Div(
            [
                create_file_preview(df, filename),
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [html.H6("📋 Data Configuration", className="mb-0")]
                        ),
                        dbc.CardBody(
                            [
                                html.P(
                                    "Configure your data for analysis:",
                                    className="mb-3",
                                ),
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button(
                                            "📋 Verify Columns",
                                            id="verify-columns-btn-simple",
                                            color="primary",
                                            size="sm",
                                        ),
                                        dbc.Button(
                                            "🤖 Classify Devices",
                                            id="classify-devices-btn",
                                            color="info",
                                            size="sm",
                                        ),
                                    ],
                                    className="w-100",
                                ),
                            ]
                        ),
                    ],
                    className="mb-3",
                ),
            ]
        )

    def process_files(
        self, contents_list: List[str] | str, filenames_list: List[str] | str
    ) -> Tuple[Any, Any, Any, Any, Any, Any, Any]:
        if not contents_list:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        self.store.clear_all()

        if not isinstance(contents_list, list):
            contents_list = [contents_list]
        if not isinstance(filenames_list, list):
            filenames_list = [filenames_list]

        upload_results: List[Any] = []
        file_preview_components: List[Any] = []
        file_info_dict: Dict[str, Any] = {}
        current_file_info: Dict[str, Any] = {}

        file_parts: Dict[str, List[str]] = {}
        for content, filename in zip(contents_list, filenames_list):
            file_parts.setdefault(filename, []).append(content)

        for filename, parts in file_parts.items():
            if len(parts) > 1:
                prefix, first = parts[0].split(",", 1)
                combined_data = first
                for part in parts[1:]:
                    _pfx, data = part.split(",", 1)
                    combined_data += data
                content = f"{prefix},{combined_data}"
            else:
                content = parts[0]

            try:
                result = process_file(content, filename)
                if result["success"]:
                    df = result["data"]
                    rows = len(df)
                    cols = len(df.columns)

                    self.store.add_file(filename, df)
                    upload_results.append(
                        self.build_success_alert(filename, rows, cols)
                    )
                    file_preview_components.append(
                        self.build_file_preview_component(df, filename)
                    )

                    column_names = df.columns.tolist()
                    file_info_dict[filename] = {
                        "filename": filename,
                        "rows": rows,
                        "columns": cols,
                        "column_names": column_names,
                        "upload_time": result["upload_time"].isoformat(),
                        "ai_suggestions": get_ai_column_suggestions(column_names),
                    }
                    current_file_info = file_info_dict[filename]

                    try:
                        learning_service = get_device_learning_service()
                        user_mappings = learning_service.get_user_device_mappings(
                            filename
                        )
                        if user_mappings:
                            from services.ai_mapping_store import ai_mapping_store

                            ai_mapping_store.clear()
                            for device, mapping in user_mappings.items():
                                mapping["source"] = "user_confirmed"
                                ai_mapping_store.set(device, mapping)
                            logger.info(
                                "✅ Loaded %s saved mappings - AI SKIPPED",
                                len(user_mappings),
                            )
                        else:
                            logger.info("🆕 First upload - AI will be used")
                            from services.ai_mapping_store import ai_mapping_store

                            ai_mapping_store.clear()
                            self.auto_apply_learned_mappings(df, filename)
                    except Exception as exc:  # pragma: no cover - best effort
                        logger.info("⚠️ Error: %s", exc)
                else:
                    upload_results.append(self.build_failure_alert(result["error"]))
            except Exception as exc:  # pragma: no cover - best effort
                upload_results.append(
                    self.build_failure_alert(f"Error processing {filename}: {str(exc)}")
                )

        upload_nav = []
        if file_info_dict:
            upload_nav = html.Div(
                [
                    html.Hr(),
                    html.H5("Ready to analyze?"),
                    dbc.Button(
                        "🚀 Go to Analytics",
                        href="/analytics",
                        color="success",
                        size="lg",
                    ),
                ]
            )

        return (
            upload_results,
            file_preview_components,
            file_info_dict,
            upload_nav,
            current_file_info,
            no_update,
            no_update,
        )


__all__ = ["UploadProcessingService"]
