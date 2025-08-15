#!/usr/bin/env python3
"""Archive cold data to object storage.

Moves files older than the configured retention period from a local
filesystem path to object storage (e.g. AWS S3) and logs the current
storage footprint to help estimate costs.
"""
from __future__ import annotations

import datetime as dt
import logging
import pathlib

import boto3
import yaml

CONFIG_PATH = pathlib.Path(__file__).resolve().parent.parent / "config" / "data_archival.yaml"


def load_config() -> dict:
    """Load archival configuration from YAML file."""
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)["archival"]


def log_storage_cost(s3: boto3.client, bucket: str) -> None:
    """Log total storage in the bucket and approximate monthly cost."""
    total_bytes = 0
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents", []):
            total_bytes += obj["Size"]
    gb = total_bytes / (1024 ** 3)
    cost = gb * 0.023  # Standard S3 pricing per GB-month
    logging.info("Current archival storage: %.2f GB (approx $%.2f/month)", gb, cost)


def archive() -> None:
    cfg = load_config()
    base_path = pathlib.Path(cfg["cold_data_path"])
    retention = dt.timedelta(days=cfg.get("retention_days", 30))
    cutoff = dt.datetime.utcnow() - retention

    storage_cfg = cfg["object_storage"]
    s3 = boto3.client("s3", region_name=storage_cfg.get("region"))
    bucket = storage_cfg["bucket"]

    archived = 0
    for file_path in base_path.rglob("*"):
        if not file_path.is_file():
            continue
        mtime = dt.datetime.utcfromtimestamp(file_path.stat().st_mtime)
        if mtime >= cutoff:
            continue
        key = file_path.relative_to(base_path).as_posix()
        s3.upload_file(str(file_path), bucket, key)
        file_path.unlink()
        archived += 1
        logging.info("Archived %s to s3://%s/%s", file_path, bucket, key)

    logging.info("Archived %d files", archived)
    log_storage_cost(s3, bucket)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    archive()
