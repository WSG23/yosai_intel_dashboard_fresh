import click

from core.callback_controller import CallbackController, CallbackEvent
from file_processing.column_mapper import (
    map_columns,
    REQUIRED_COLUMNS,
    OPTIONAL_COLUMNS,
)
from file_processing.data_processor import DataProcessor
from file_processing.format_detector import FormatDetector
from file_processing.readers import (
    CSVReader,
    JSONReader,
    ExcelReader,
    FWFReader,
    ArchiveReader,
)


@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--hint", default=None, help="Optional metadata hint")
def review(input_path: str, hint: str | None) -> None:
    """CLI to review and confirm fuzzy column/device mappings."""

    detector = FormatDetector(
        [CSVReader(), JSONReader(), ExcelReader(), FWFReader(), ArchiveReader()]
    )
    df, meta = detector.detect_and_load(input_path, hint={"hint": hint})

    canonical = {name: [] for name in REQUIRED_COLUMNS + OPTIONAL_COLUMNS}

    col_controller = CallbackController()
    col_warnings: list[dict] = []

    def collect_col(ctx):
        if ctx.event_type == CallbackEvent.SYSTEM_WARNING and "column" in ctx.data:
            col_warnings.append(
                {
                    "column": ctx.data["column"],
                    "candidates": ctx.data.get("suggestions", []),
                }
            )

    col_controller.register_callback(CallbackEvent.SYSTEM_WARNING, collect_col)
    df_cols = map_columns(df, canonical, fuzzy_threshold=80, controller=col_controller)

    for warn in col_warnings:
        candidates = warn.get("candidates", [])
        default = candidates[0] if candidates else warn["column"]
        click.echo(f"Column '{warn['column']}' matches: {candidates}")
        choice = click.prompt(
            "Choose index or enter custom name",
            default=default,
        )
        df_cols = df_cols.rename(columns={warn["column"]: choice})

    processor = DataProcessor()
    dev_controller = processor.callback_controller
    dev_warnings: list[dict] = []

    def collect_dev(ctx):
        if (
            ctx.source_id == "device_enrichment"
            and ctx.event_type == CallbackEvent.SYSTEM_WARNING
        ):
            dev_warnings.append({"value": ctx.data.get("value"), "candidates": []})

    dev_controller.register_callback(CallbackEvent.SYSTEM_WARNING, collect_dev)
    processor._enrich_devices(df_cols)

    for warn in dev_warnings:
        click.echo(
            f"Device '{warn['value']}' unmatched; top matches: {warn['candidates']}"
        )
        choice = click.prompt("Enter canonical device_id", default="")
        if choice:
            processor.device_registry.setdefault(choice, {})
            df_cols["device_id"] = df_cols["device_name"].apply(
                lambda v, src=warn["value"]: choice if v == src else v
            )

    if hasattr(processor.device_registry, "update_aliases_from_confirmation"):
        processor.device_registry.update_aliases_from_confirmation({})

    click.echo("Mappings updated.")


if __name__ == "__main__":  # pragma: no cover
    review()
