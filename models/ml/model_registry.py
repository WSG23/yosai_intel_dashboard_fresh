from __future__ import annotations

import os
import logging
from datetime import datetime
from typing import Any, Dict, List

import boto3
import mlflow
from packaging.version import Version
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    JSON,
    String,
    create_engine,
    select,
    update,
)
from sqlalchemy.orm import declarative_base, sessionmaker

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
    dataset_hash = Column(String(64))
    storage_uri = Column(String(255))
    mlflow_run_id = Column(String(64))
    is_active = Column(Boolean, default=False)


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
        self.s3 = s3_client or boto3.client("s3")
        self.bucket = bucket
        if mlflow_uri:
            mlflow.set_tracking_uri(mlflow_uri)
        self.metric_thresholds = metric_thresholds or {}

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

            key = f"{name}/{version}/{os.path.basename(model_path)}"
            self.s3.upload_file(model_path, self.bucket, key)
            storage_uri = f"s3://{self.bucket}/{key}"

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
                    dataset_hash=dataset_hash,
                    storage_uri=storage_uri,
                    mlflow_run_id=run_id,
                    is_active=False,
                )
                session.add(record)
                session.commit()
                session.refresh(record)
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

    # --------------------------------------------------------------
    def download_artifact(self, storage_uri: str, destination: str) -> None:
        if storage_uri.startswith("s3://"):
            path = storage_uri[5:]
            bucket, key = path.split("/", 1)
            self.s3.download_file(bucket, key, destination)


__all__ = ["ModelRegistry", "ModelRecord", "Base"]
