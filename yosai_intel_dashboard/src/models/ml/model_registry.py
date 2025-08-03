import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import pandas as pd
from packaging.version import Version
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
    select,
    update,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from optional_dependencies import import_optional

boto3 = import_optional("boto3")
mlflow = import_optional("mlflow")
requests = import_optional("requests")

logger = logging.getLogger(__name__)

Base = declarative_base()


class ModelRecord(Base):
    """ORM model for storing ML models."""

    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    version = Column(String(20), nullable=False)
    training_date = Column(DateTime, default=datetime.utcnow)
    metrics = Column(JSON)
    accuracy = Column(Float)
    dataset_hash = Column(String(64))
    storage_uri = Column(String(255))
    mlflow_run_id = Column(String(64))
    is_active = Column(Boolean, default=False)


class PredictionExplanationRecord(Base):
    """ORM model for storing prediction explanations."""

    __tablename__ = "prediction_explanations"

    id = Column(Integer, primary_key=True)
    prediction_id = Column(String(64), unique=True, nullable=False)
    model_name = Column(String(128), nullable=False)
    model_version = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    explanation = Column(JSON, nullable=False)


class ModelRegistry:
    """Simple model registry using SQLAlchemy and S3 storage."""

    def __init__(
        self,
        database_url: str,
        bucket: str,
        *,
        s3_client: Any | None = None,
        mlflow_uri: str | None = None,
        metric_thresholds: Dict[str, float] | None = None,
    ) -> None:
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        if s3_client is not None:
            self.s3 = s3_client
        elif boto3:
            self.s3 = boto3.client("s3")
        else:  # pragma: no cover - missing optional dependency
            raise RuntimeError("boto3 is required for S3 storage")
        self.bucket = bucket
        if mlflow_uri and mlflow:
            mlflow.set_tracking_uri(mlflow_uri)
        elif mlflow_uri:
            raise RuntimeError("mlflow is required for tracking")
        self.metric_thresholds = metric_thresholds or {}
        self._baseline_features: Dict[str, pd.DataFrame] = {}
        self._latest_features: Dict[str, pd.DataFrame] = {}

    # --------------------------------------------------------------
    def _metrics_improved(self, new: Dict[str, float], old: Dict[str, float]) -> bool:
        for key, threshold in self.metric_thresholds.items():
            if key in new and key in old and (new[key] - old[key]) >= threshold:
                return True
        return False

    def _bump_version(self, current: str, improved: bool) -> str:
        ver = Version(current)
        major, minor, patch = ver.major, ver.minor, ver.micro
        if improved:
            minor += 1
            patch = 0
        else:
            patch += 1
        return f"{major}.{minor}.{patch}"

    def _session(self):
        return self.Session()

    # --------------------------------------------------------------
    def register_model(
        self,
        name: str,
        model_path: str,
        metrics: Dict[str, float],
        dataset_hash: str,
        *,
        version: str | None = None,
        training_date: datetime | None = None,
    ) -> ModelRecord:
        session = self._session()
        try:
            active = self.get_model(name, active_only=True)
            if version is None:
                if active:
                    improved = self._metrics_improved(metrics, active.metrics or {})
                    version = self._bump_version(active.version, improved)
                else:
                    version = "0.1.0"

            key = f"{name}/{version}/{Path(model_path).name}"
            self.s3.upload_file(model_path, self.bucket, key)
            storage_uri = f"s3://{self.bucket}/{key}"

            if not mlflow:
                raise RuntimeError("mlflow is required to register models")
            with mlflow.start_run() as run:
                for k, v in metrics.items():
                    mlflow.log_metric(k, v)
                mlflow.log_artifact(model_path)
                run_id = run.info.run_id

                record = ModelRecord(
                    name=name,
                    version=version,
                    training_date=training_date or datetime.utcnow(),
                    metrics=metrics,
                    accuracy=metrics.get("accuracy"),
                    dataset_hash=dataset_hash,
                    storage_uri=storage_uri,
                    mlflow_run_id=run_id,
                    is_active=False,
                )
                session.add(record)
                session.commit()
                session.refresh(record)

                # Keep only the five most recent versions per model
                stmt = (
                    select(ModelRecord)
                    .where(ModelRecord.name == name)
                    .order_by(ModelRecord.training_date.desc())
                )
                versions = session.execute(stmt).scalars().all()
                for old in versions[5:]:
                    session.delete(old)
                if len(versions) > 5:
                    session.commit()

                return record
        finally:
            session.close()

    # --------------------------------------------------------------
    def get_model(
        self,
        name: str,
        version: str | None = None,
        *,
        active_only: bool = False,
    ) -> ModelRecord | None:
        session = self._session()
        try:
            stmt = select(ModelRecord).where(ModelRecord.name == name)
            if active_only:
                stmt = stmt.where(ModelRecord.is_active.is_(True))
            if version:
                stmt = stmt.where(ModelRecord.version == version)
            stmt = stmt.order_by(ModelRecord.version.desc())
            result = session.execute(stmt).scalars().first()
            return result
        finally:
            session.close()

    def list_models(self, name: str | None = None) -> List[ModelRecord]:
        session = self._session()
        try:
            stmt = select(ModelRecord)
            if name:
                stmt = stmt.where(ModelRecord.name == name)
            stmt = stmt.order_by(ModelRecord.name, ModelRecord.version)
            return list(session.execute(stmt).scalars().all())
        finally:
            session.close()

    def list_versions(self, name: str) -> List[ModelRecord]:
        """Return all versions for a given model name."""
        return self.list_models(name)

    def delete_model(self, model_id: int) -> None:
        session = self._session()
        try:
            record = session.get(ModelRecord, model_id)
            if record:
                session.delete(record)
                session.commit()
        finally:
            session.close()

    def set_active_version(self, name: str, version: str) -> None:
        session = self._session()
        try:
            session.execute(
                update(ModelRecord)
                .where(ModelRecord.name == name)
                .values(is_active=False)
            )
            session.execute(
                update(ModelRecord)
                .where(ModelRecord.name == name, ModelRecord.version == version)
                .values(is_active=True)
            )
            session.commit()
        finally:
            session.close()

    def rollback_to_previous(self, name: str) -> ModelRecord | None:
        session = self._session()
        try:
            stmt = (
                select(ModelRecord)
                .where(ModelRecord.name == name)
                .order_by(ModelRecord.version.desc())
            )
            records = session.execute(stmt).scalars().all()
            target = next((r for r in records if not r.is_active), None)
            if target is None:
                return None
            session.execute(
                update(ModelRecord)
                .where(ModelRecord.name == name)
                .values(is_active=False)
            )
            session.execute(
                update(ModelRecord)
                .where(ModelRecord.id == target.id)
                .values(is_active=True)
            )
            session.commit()
            session.refresh(target)
            return target
        finally:
            session.close()

    # --------------------------------------------------------------
    def download_artifact(self, storage_uri: str, destination: str) -> None:
        parsed = urlparse(storage_uri)
        scheme = parsed.scheme

        if scheme == "s3":
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")
            self.s3.download_file(bucket, key, destination)
        elif scheme in ("file", ""):
            src = parsed.path if scheme == "file" else storage_uri
            shutil.copy(src, destination)
        elif scheme in ("http", "https"):
            if not requests:
                raise RuntimeError("requests is required for HTTP downloads")
            resp = requests.get(storage_uri, stream=True)
            resp.raise_for_status()
            with open(destination, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        fh.write(chunk)
        else:
            raise ValueError(f"Unsupported storage URI scheme: {scheme}")

    # --------------------------------------------------------------
    def log_features(self, name: str, features: pd.DataFrame) -> None:
        """Store the latest feature values for drift monitoring."""
        if name not in self._baseline_features:
            self._baseline_features[name] = features
        self._latest_features[name] = features

    def get_drift_metrics(self, name: str, bins: int = 10) -> Dict[str, float]:
        """Return Population Stability Index metrics for *name*."""
        base = self._baseline_features.get(name)
        current = self._latest_features.get(name)
        if base is None or current is None:
            return {}
        from yosai_intel_dashboard.src.services.monitoring.drift import compute_psi

        return compute_psi(base, current, bins=bins)

    # --------------------------------------------------------------
    def log_explanation(
        self,
        prediction_id: str,
        model_name: str,
        model_version: str,
        explanation: Dict[str, Any],
    ) -> None:
        """Persist a SHAP explanation record."""
        session = self._session()
        try:
            record = PredictionExplanationRecord(
                prediction_id=prediction_id,
                model_name=model_name,
                model_version=model_version,
                explanation=explanation,
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

    def get_explanation(self, prediction_id: str) -> Dict[str, Any] | None:
        """Retrieve a stored explanation by prediction id."""
        session = self._session()
        try:
            stmt = select(PredictionExplanationRecord).where(
                PredictionExplanationRecord.prediction_id == prediction_id
            )
            record = session.execute(stmt).scalar_one_or_none()
            if record is None:
                return None
            return {
                "prediction_id": record.prediction_id,
                "model_name": record.model_name,
                "model_version": record.model_version,
                "timestamp": record.timestamp,
                "explanation": record.explanation,
            }
        finally:
            session.close()


__all__ = [
    "ModelRegistry",
    "ModelRecord",
    "PredictionExplanationRecord",
    "Base",
]
