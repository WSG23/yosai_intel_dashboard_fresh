from __future__ import annotations

"""Simplified analytics service with explicit type annotations for mypy."""

from typing import Any, Dict

class AnalyticsService:
    """Minimal service returning placeholder analytics data."""

    def __init__(self) -> None:
        self._metrics: Dict[str, Any] = {}

    def get_analytics(self, source: str) -> Dict[str, Any]:
        """Return dummy analytics information for ``source``."""
        return {"source": source, "status": "ok"}

    def process_dataframe(self, df: Any) -> Dict[str, Any]:
        """Return the number of rows in ``df`` if available."""
        rows = getattr(df, "shape", (0,))[0]
        return {"rows": rows}

    def get_metrics(self) -> Dict[str, Any]:
        """Return current analytics metrics."""
        return self.get_analytics_status()

    # ------------------------------------------------------------------
    # Placeholder implementations for abstract methods
    # ------------------------------------------------------------------
    @override
    def analyze_access_patterns(
        self, days: int, user_id: str | None = None
    ) -> Dict[str, Any]:
        """Analyze access patterns over the given timeframe."""
        logger.debug(
            f"analyze_access_patterns called with days={days} user_id={user_id}"
        )
        return {"patterns": [], "days": days, "user_id": user_id}

    @override
    def detect_anomalies(
        self, data: pd.DataFrame, sensitivity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in the provided data."""
        logger.debug(f"detect_anomalies called with sensitivity={sensitivity}")
        return []

    @override
    def generate_report(
        self, report_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate an analytics report."""
        logger.debug(
            f"generate_report called with report_type={report_type} params={params}"
        )
        return {"report_type": report_type, "params": params}

    # ------------------------------------------------------------------
    def load_model_from_registry(
        self, name: str, *, destination_dir: Path | None = None
    ) -> Path | None:
        """Download the active model from the registry."""
        if self.model_registry is None:
            return None
        record = self.model_registry.get_model(name, active_only=True)
        if record is None:
            return None
        models_path = getattr(self.config, "analytics", None)
        base_dir: Path = destination_dir or Path(
            getattr(models_path, "ml_models_path", "models/ml")
        )
        dest = base_dir / name / record.version
        dest.mkdir(parents=True, exist_ok=True)
        local_path = dest / Path(record.storage_uri).name
        local_version = self.model_registry.get_version_metadata(name)
        if local_version == record.version and local_path.exists():
            return local_path
        try:
            self.model_registry.download_artifact(
                record.storage_uri,
                local_path,
            )
            self.model_registry.store_version_metadata(name, record.version)
            return local_path
        except (
            OSError,
            RuntimeError,
            requests.RequestException,
            ValueError,
        ) as exc:  # pragma: no cover - best effort
            logger.error(
                f"Failed to download model {name} ({type(exc).__name__}): {exc}"
            )
            return None


# Global service instance
_analytics_service: AnalyticsService | None = None
_analytics_service_lock = threading.Lock()


def get_analytics_service(
    service: AnalyticsService | None = None,
    config_provider: ConfigProviderProtocol | None = None,
    model_registry: ModelRegistry | None = None,
) -> AnalyticsService:
    """Return a global analytics service instance.

    If ``service`` is provided, it becomes the global instance.  Otherwise an
    instance is created on first access.
    """
    global _analytics_service
    if service is not None:
        with _analytics_service_lock:
            _analytics_service = service
        return _analytics_service
    if _analytics_service is None:
        with _analytics_service_lock:
            if _analytics_service is None:
                _analytics_service = create_analytics_service(
                    config_provider=config_provider,
                    model_registry=model_registry,
                )
    return _analytics_service


def create_analytics_service(
    config_provider: ConfigProviderProtocol | None = None,
    model_registry: ModelRegistry | None = None,
) -> AnalyticsService:
    """Create new analytics service instance with default dependencies."""

    validation = SecurityValidator()
    processor = Processor(validator=validation)
    upload_service = get_upload_data_service()
    upload_processor = UploadAnalyticsProcessor(validation, processor)
    upload_controller = UploadProcessingController(
        validation,
        processor,
        upload_service,
        upload_processor,
    )
    loader = get_analytics_data_loader(upload_controller, processor)
    report_generator = SummaryReportGenerator()
    calculator = Calculator(report_generator)
    publisher = PublishingService()
    return AnalyticsService(
        data_processor=processor,
        config=config_provider,
        upload_data_service=upload_service,
        model_registry=model_registry,
        loader=loader,
        calculator=calculator,
        publisher=publisher,
        report_generator=report_generator,
        upload_controller=upload_controller,
        upload_processor=upload_processor,
    )


class RiskScoreResult(NamedTuple):
    """Simple risk score container."""

    score: float
    level: str


def _risk_level(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    return "low"


def calculate_risk_score(
    anomaly_component: float = 0.0,
    pattern_component: float = 0.0,
    behavior_component: float = 0.0,
) -> RiskScoreResult:
    """Combine numeric risk components into a final score."""

    score = (
        max(0.0, min(anomaly_component, 100.0))
        + max(0.0, min(pattern_component, 100.0))
        + max(0.0, min(behavior_component, 100.0))
    ) / 3
    score = round(score, 2)
    return RiskScoreResult(score=score, level=_risk_level(score))



def get_analytics_service() -> AnalyticsService:
    """Provide a default :class:`AnalyticsService` instance."""
    return AnalyticsService()
