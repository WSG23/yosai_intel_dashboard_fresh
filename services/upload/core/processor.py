import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import dash
import dash.html as html
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dash import no_update

from components.file_preview import create_file_preview_ui
from services.async_file_processor import AsyncFileProcessor
from services.data_enhancer import get_ai_column_suggestions
from services.interfaces import (
    UploadDataServiceProtocol,
    get_device_learning_service,
)
from services.upload.utils.file_parser import create_file_preview
from services.upload_data_service import UploadDataService
from utils.upload_store import UploadedDataStore

from ..async_processor import AsyncUploadProcessor
from ..protocols import (
    DeviceLearningServiceProtocol,
    FileProcessorProtocol,
    UploadProcessingServiceProtocol,
    UploadStorageProtocol,
    UploadValidatorProtocol,
)

logger = logging.getLogger(__name__)


class UploadProcessingService(UploadProcessingServiceProtocol):
    """Service handling processing of uploaded files."""

    def __init__(
        self,
        store: UploadStorageProtocol,
        learning_service: DeviceLearningServiceProtocol,
        data_service: UploadDataServiceProtocol | None = None,
        processor: Optional[FileProcessorProtocol] = None,
        validator: Optional[UploadValidatorProtocol] = None,
    ) -> None:
        self.store = store
        self.learning_service = learning_service
        self.data_service = data_service or UploadDataService(store)
        self.processor = processor or AsyncFileProcessor()
        self.validator = validator
        self.async_processor = AsyncUploadProcessor()

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
                        html.I(
                            className="fas fa-check-circle me-2",
                            **{"aria-hidden": "true"},
                        ),
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
            learned = self.learning_service.get_learned_mappings(df, filename)
            if learned:
                self.learning_service.apply_learned_mappings_to_global_store(
                    df, filename
                )
                logger.info("🤖 Auto-applied %s learned device mappings", len(learned))
                return True
            return False
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Failed to auto-apply learned mappings: %s", exc)
            return False

    def build_file_preview_component(self, df: pd.DataFrame, filename: str) -> html.Div:
        preview_info = create_file_preview(df)
        return html.Div(
            [
                create_file_preview_ui(preview_info),
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

    async def process_uploaded_files(
        self,
        contents_list: List[str] | str,
        filenames_list: List[str] | str,
        *,
        task_progress: Callable[[int], None] | None = None,
        return_format: str = "legacy",
    ) -> Dict[str, Any] | Tuple:
        """Flexible upload processor supporting unlimited metafile types"""

        if not contents_list:
            empty_result = {
                "upload_results": [],
                "file_info_dict": {},
                "current_file_info": {},
                "file_preview_components": [],
                "upload_nav": [],
                "metadata": {},
                "ai_suggestions": {},
                "device_mappings": {},
                "validation_results": {},
                "processing_stats": {},
                "extensions": {},
            }
            return self._format_return(empty_result, return_format)

        self.store.clear_all()

        if not isinstance(contents_list, list):
            contents_list = [contents_list]
        if not isinstance(filenames_list, list):
            filenames_list = [filenames_list]

        # Flexible result container - can expand for any metafile type
        result = {
            "upload_results": [],
            "file_preview_components": [],
            "file_info_dict": {},
            "current_file_info": {},
            "upload_nav": [],
            "metadata": {},
            "ai_suggestions": {},
            "device_mappings": {},
            "validation_results": {},
            "processing_stats": {},
            "extensions": {},
        }

        file_parts: Dict[str, List[str]] = {}
        for content, filename in zip(contents_list, filenames_list):
            file_parts.setdefault(filename, []).append(content)

        total_files = len(file_parts)
        processed_files = 0

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

                def _cb(name: str, pct: int) -> None:
                    if task_progress:
                        overall = int(
                            ((processed_files + pct / 100) / total_files) * 100
                        )
                        task_progress(overall)

                df = await self.processor.process_file(
                    content, filename, progress_callback=_cb
                )
                rows = len(df)
                cols = len(df.columns)

                self.store.add_file(filename, df)
                result["upload_results"].append(
                    self.build_success_alert(filename, rows, cols)
                )
                result["file_preview_components"].append(
                    self.build_file_preview_component(df, filename)
                )

                column_names = df.columns.tolist()
                file_info = {
                    "filename": filename,
                    "rows": rows,
                    "columns": cols,
                    "column_names": column_names,
                    "upload_time": pd.Timestamp.now().isoformat(),
                    "ai_suggestions": get_ai_column_suggestions(column_names),
                }

                result["file_info_dict"][filename] = file_info
                result["current_file_info"] = file_info
                result["ai_suggestions"][filename] = file_info["ai_suggestions"]

                # Handle device mappings
                try:
                    user_mappings = self.learning_service.get_user_device_mappings(
                        filename
                    )
                    if user_mappings:
                        from services.ai_mapping_store import ai_mapping_store

                        ai_mapping_store.clear()
                        for device, mapping in user_mappings.items():
                            mapping["source"] = "user_confirmed"
                            ai_mapping_store.set(device, mapping)
                        result["device_mappings"][filename] = user_mappings
                        logger.info(
                            "✅ Loaded %s saved mappings - AI SKIPPED",
                            len(user_mappings),
                        )
                    else:
                        logger.info("🆕 First upload - AI will be used")
                        from services.ai_mapping_store import ai_mapping_store

                        ai_mapping_store.clear()
                        self.auto_apply_learned_mappings(df, filename)
                        result["device_mappings"][filename] = {}
                except Exception as exc:
                    logger.info("⚠️ Error: %s", exc)
                    result["validation_results"][filename] = {"error": str(exc)}

            except Exception as exc:
                result["upload_results"].append(
                    self.build_failure_alert(f"Error processing {filename}: {str(exc)}")
                )
                result["validation_results"][filename] = {"error": str(exc)}

            processed_files += 1
            if task_progress:
                pct = int(processed_files / total_files * 100)
                task_progress(pct)

        # Add navigation if files processed
        if result["file_info_dict"]:
            result["upload_nav"] = html.Div(
                [
                    html.Hr(),
                    html.H5("Ready for device analysis?"),
                    dbc.Button(
                        "🚀 Start Device Analysis",
                        href="/device-analysis",
                        color="success",
                        size="lg",
                    ),
                ]
            )

        # Add processing statistics
        result["processing_stats"] = {
            "total_files": total_files,
            "processed_files": processed_files,
            "total_rows": sum(
                info.get("rows", 0) for info in result["file_info_dict"].values()
            ),
            "total_columns": sum(
                info.get("columns", 0) for info in result["file_info_dict"].values()
            ),
        }

        return self._format_return(result, return_format)

    def _format_return(self, result: Dict[str, Any], return_format: str):
        """Format return based on caller needs - infinitely flexible"""
        if return_format == "dict":
            return result
        elif return_format == "simple":
            # For simple callers like mde.py - return just 3 core values
            return result
        elif return_format == "legacy":
            # For legacy dashboard callers expecting exactly 7 values
            return result
        elif return_format == "extended":
            # For future metafile processors that need more data
            return result
        else:
            # Default: return full dictionary for maximum flexibility
            return result

    # Backwards compatibility alias

    async def process_files(
        self,
        contents_list: List[str] | str,
        filenames_list: List[str] | str,
        *,
        task_progress: Callable[[int], None] | None = None,
    ) -> Dict[str, Any]:
        """FLEXIBLE - returns dictionary, never fixed tuple"""
        return await self.process_uploaded_files(
            contents_list,
            filenames_list,
            task_progress=task_progress,
            return_format="dict",
        )
