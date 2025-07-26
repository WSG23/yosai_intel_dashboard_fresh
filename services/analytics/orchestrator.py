from __future__ import annotations

"""Coordinator for analytics services."""

import asyncio
from typing import Any, Dict, List
import pandas as pd

from .core.interfaces import (
    LoaderProtocol,
    ValidatorProtocol,
    TransformerProtocol,
    CalculatorProtocol,
    AggregatorProtocol,
    AnalyzerProtocol,
    RepositoryProtocol,
    EventPublisherProtocol,
)


class AnalyticsOrchestrator:
    """Coordinate analytics components via dependency injection."""

    def __init__(
        self,
        loader: LoaderProtocol,
        validator: ValidatorProtocol,
        transformer: TransformerProtocol,
        calculator: CalculatorProtocol,
        aggregator: AggregatorProtocol,
        analyzer: AnalyzerProtocol,
        repository: RepositoryProtocol,
        publisher: EventPublisherProtocol,
    ) -> None:
        self.loader = loader
        self.validator = validator
        self.transformer = transformer
        self.calculator = calculator
        self.aggregator = aggregator
        self.analyzer = analyzer
        self.repository = repository
        self.publisher = publisher

    # ------------------------------------------------------------------
    def get_dashboard_summary(self) -> Dict[str, Any]:
        data = self.loader.load_uploaded_data()
        if not data:
            return {"status": "no_data"}
        df = pd.concat(list(data.values()), ignore_index=True)
        df = self.transformer.transform(df)
        summary = self.loader.summarize_dataframe(df)
        self.publisher.publish(summary)
        return summary

    # ------------------------------------------------------------------
    def process_uploaded_data_directly(self, uploaded: Dict[str, Any]) -> Dict[str, Any]:
        return self.loader.controller.process_uploaded_data_directly(uploaded)  # type: ignore[attr-defined]

    async def aprocess_uploaded_data_directly(self, uploaded: Dict[str, Any]) -> Dict[str, Any]:
        return await asyncio.to_thread(self.process_uploaded_data_directly, uploaded)

    # ------------------------------------------------------------------
    def regular_analysis(self, df: pd.DataFrame, analysis_types: List[str]) -> Dict[str, Any]:
        from services.result_formatting import regular_analysis

        return regular_analysis(df, analysis_types)

    def get_real_uploaded_data(self) -> Dict[str, Any]:
        return self.loader.get_real_uploaded_data()

    def get_analytics_with_fixed_processor(self) -> Dict[str, Any]:
        return self.loader.get_analytics_with_fixed_processor()

    def get_database_analytics(self) -> Dict[str, Any]:
        return self.repository.get_analytics()

    def get_unique_patterns_analysis(self, data_source: str | None = None) -> Dict[str, Any]:
        df, original_rows = self.loader.load_patterns_dataframe(data_source)
        if df.empty:
            return {"status": "no_data", "message": "No uploaded files available", "data_summary": {"total_records": 0}}
        result = self.analyzer.analyze(df, original_rows)
        self.publisher.publish(result)
        return result


__all__ = ["AnalyticsOrchestrator"]
