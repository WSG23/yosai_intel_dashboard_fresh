"""CLI helpers for reviewing fuzzy mappings."""

import click

from .column_mapper import MappingWarning, map_columns
from .data_processor import DataProcessor
from .format_detector import FormatDetector


@click.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option("--hint", default=None, help="Optional ingest hint")
def review(input_path: str, hint: str | None) -> None:
    """CLI to confirm fuzzy column and device mappings before export."""
    detector = FormatDetector()
    df, meta = detector.detect_and_load(input_path, {"hint": hint})

    df, col_warnings = map_columns(df, threshold=80, collect_warnings=True)
    for w in col_warnings:
        click.echo(f"Column '{w.column}' candidates: {w.candidates}")
        choice = click.prompt("Select mapping or enter custom", default=w.candidates[0])
        df = df.rename(columns={w.column: choice})

    processor = DataProcessor(
        config=meta.get("config"), device_registry=meta.get("device_registry")
    )
    _, dev_warnings = processor._collect_device_warnings(df)
    for w in dev_warnings:
        click.echo(f"Device '{w.value}' candidates: {w.candidates}")
        choice = click.prompt("Enter correct device_id", default="")
        df["device_id"] = df["device_name"].apply(
            lambda v, src=w.value: choice if v == src else v
        )

    processor.device_registry.persist_aliases()
    click.echo("Mappings confirmed and saved.")


if __name__ == "__main__":  # pragma: no cover
    review()
