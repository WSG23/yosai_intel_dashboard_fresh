from __future__ import annotations

"""Prefect orchestration for access event processing pipeline."""

import prefect
from prefect import Flow, task

from file_processing.format_detector import FormatDetector, UnsupportedFormatError
from file_processing.data_processor import DataProcessor
from file_processing.exporter import export_to_csv, export_to_json, ExportError
from core.callback_controller import CallbackController, CallbackEvent


@task
def ingest(file_path: str, hint: dict | None = None):
    """Load input file based on detected format."""
    detector = FormatDetector()
    try:
        df, meta = detector.detect_and_load(file_path, hint)
    except UnsupportedFormatError as exc:
        CallbackController().fire_event(
            CallbackEvent.FILE_PROCESSING_ERROR,
            file_path,
            {"error": str(exc)},
        )
        raise
    return df, meta


@task
def transform(df, meta, config, device_registry, callback_controller):
    """Transform DataFrame according to provided configuration."""
    processor = DataProcessor(config, device_registry, callback_controller)
    df2 = processor.process(df, meta)
    return df2, meta


@task
def export(df, meta, output_base: str):
    """Export processed data to CSV and JSON outputs."""
    try:
        export_to_csv(df, f"{output_base}.csv", meta)
        export_to_json(df, f"{output_base}.json", meta)
    except ExportError as exc:
        CallbackController().fire_event(
            CallbackEvent.FILE_PROCESSING_ERROR,
            output_base,
            {"error": str(exc)},
        )
        raise


with Flow("access-event-pipeline") as flow:
    file_path = prefect.Parameter("file_path")
    hint = prefect.Parameter("hint", default=None)
    output_base = prefect.Parameter("output_base")
    config = prefect.Parameter("config")
    device_registry = prefect.Parameter("device_registry")
    callback_controller = prefect.Parameter("callback_controller")

    df, meta = ingest(file_path, hint)
    df2, meta2 = transform(df, meta, config, device_registry, callback_controller)
    export(df2, meta2, output_base)


if __name__ == "__main__":
    # Example runner: load config, registry, callback controller then run the flow
    pass
