"""Configuration classes for the AI Classification plugin"""

import os
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class CSVProcessingConfig:
    sample_size: int = 1000
    max_file_size_mb: int = 100
    supported_encodings: List[str] = field(
        default_factory=lambda: [
            "utf-8",
            "shift_jis",
            "euc-jp",
            "iso-2022-jp",
        ]
    )
    chunk_size: int = 10000


@dataclass
class ColumnMappingConfig:
    min_confidence_threshold: float = 0.3
    auto_confirm_threshold: float = 0.9
    learning_enabled: bool = True
    model_path: str = "data/column_model.joblib"
    vectorizer_path: str = "data/column_vectorizer.joblib"


@dataclass
class FloorEstimationConfig:
    min_locations_for_estimation: int = 5
    max_floors_heuristic: int = 50


@dataclass
class EntryClassificationConfig:
    security_level_factors: Dict[str, float] = field(
        default_factory=lambda: {
            "time_of_day": 0.3,
            "location_type": 0.4,
            "access_frequency": 0.3,
        }
    )


@dataclass
class JapaneseConfig:
    enabled: bool = True
    use_mecab: bool = True
    fallback_encoding: str = "shift_jis"


@dataclass
class DatabaseConfig:
    path: str = "data/ai_classification.db"
    csv_path: str = "data/csv_storage.db"
    backup_enabled: bool = True


@dataclass
class AIClassificationConfig:
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    csv_processing: CSVProcessingConfig = field(default_factory=CSVProcessingConfig)
    column_mapping: ColumnMappingConfig = field(default_factory=ColumnMappingConfig)
    floor_estimation: FloorEstimationConfig = field(
        default_factory=FloorEstimationConfig
    )
    entry_classification: EntryClassificationConfig = field(
        default_factory=EntryClassificationConfig
    )
    japanese: JapaneseConfig = field(default_factory=JapaneseConfig)


def get_ai_config() -> AIClassificationConfig:
    cfg = AIClassificationConfig()
    if os.getenv("AI_DB_PATH"):
        cfg.database.path = os.getenv("AI_DB_PATH")
    if os.getenv("CSV_DB_PATH"):
        cfg.database.csv_path = os.getenv("CSV_DB_PATH")
    return cfg
