from __future__ import annotations

"""Prefect orchestration for access event processing pipeline."""

from prefect import Flow, Parameter, task

from core.callback_controller import CallbackController
from file_processing.data_processor import DataProcessor
from file_processing.exporter import ExportError, export_to_csv, export_to_json
from file_processing.format_detector import FormatDetector, UnsupportedFormatError


@task
def ingest(file_path: str, hint: dict):
    """Load the input file and detect its format."""
    cb = CallbackController()
    try:
        df, meta = FormatDetector().detect_and_load(file_path, hint)
        return df, meta
    except UnsupportedFormatError as e:
        cb.error(f"Ingestion failed: {e}", context={"file": file_path})
        raise


@task
def transform(df, meta, config, registry):
    """Transform the dataframe using :class:`DataProcessor`."""
    processor = DataProcessor(config, registry)
    df2 = processor.process(df, meta)
    return df2, meta


@task
def export(df, meta, output_base: str):
    """Export the processed data to CSV and JSON."""
    cb = CallbackController()
    try:
        export_to_csv(df, f"{output_base}.csv", meta)
        export_to_json(df, f"{output_base}.json", meta)
        cb.info("Export succeeded", context={"output": output_base})
    except ExportError as e:
        cb.error(f"Export failed: {e}", context={"base": output_base})
        raise


with Flow("access-event-pipeline") as flow:
    file_path = Parameter("file_path")
    hint = Parameter("hint", default={})
    output_base = Parameter("output_base")
    config = Parameter("config")
    registry = Parameter("device_registry")

    df, meta = ingest(file_path, hint)
    df2, meta = transform(df, meta, config, registry)
    export(df2, meta, output_base)


if __name__ == "__main__":  # pragma: no cover - manual execution example
    import json

    import yaml

    # load config and registry ...
    flow.run(
        parameters={
            "file_path": "path/to/data.csv",
            "output_base": "out/data",
            "config": config,
            "device_registry": registry,
        }
    )
