import sys
import types
import pandas as pd
from sklearn.ensemble import IsolationForest

dash_stub = types.ModuleType("dash")
setattr(dash_stub, "Dash", object)
deps_stub = types.ModuleType("dependencies")
for attr in ["Input", "Output", "State"]:
    setattr(deps_stub, attr, object)
setattr(dash_stub, "dependencies", deps_stub)
setattr(dash_stub, "no_update", object())
sys.modules.setdefault("dash", dash_stub)
sys.modules.setdefault("dash.dependencies", deps_stub)
sys.modules.setdefault("redis", types.ModuleType("redis"))
sys.modules.setdefault("redis.asyncio", types.ModuleType("redis.asyncio"))
sys.modules.setdefault("hvac", types.ModuleType("hvac"))

from analytics.anomaly_detection.data_prep import prepare_anomaly_data
from analytics.anomaly_detection.ml_inference import detect_ml_anomalies
import importlib.util
from pathlib import Path

MODULE_DIR = Path(__file__).resolve().parents[3] / "models"
spec = importlib.util.spec_from_file_location(
    "anomaly_models", MODULE_DIR / "anomaly_models.py"
)
anomaly_models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anomaly_models)
train_dbscan_model = anomaly_models.train_dbscan_model
train_autoencoder_model = anomaly_models.train_autoencoder_model


def test_prepare_anomaly_data_basic():
    df = pd.DataFrame({
        "timestamp": ["2024-01-01 00:00:00"],
        "person_id": ["u1"],
        "door_id": ["d1"],
        "access_result": ["Granted"],
    })
    cleaned = prepare_anomaly_data(df)
    assert "hour" in cleaned.columns
    assert cleaned["access_granted"].iloc[0] == 1


def test_detect_ml_anomalies_runs():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=20, freq="min"),
        "person_id": ["u1"] * 20,
        "door_id": ["d1"] * 20,
        "access_result": ["Granted"] * 20,
    })
    cleaned = prepare_anomaly_data(df)
    model = IsolationForest(random_state=42, n_estimators=10, contamination=0.1)
    anomalies = detect_ml_anomalies(cleaned, 0.9, model)
    assert isinstance(anomalies, list)


def test_train_models_and_ensemble():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=30, freq="min"),
        "person_id": ["u1"] * 30,
        "door_id": ["d1"] * 30,
        "access_result": ["Granted"] * 30,
    })
    cleaned = prepare_anomaly_data(df)
    iso = IsolationForest(random_state=42, n_estimators=10, contamination=0.1)
    db_model, db_scaler = train_dbscan_model(cleaned, eps=0.5, min_samples=3)
    ae_model, ae_scaler = train_autoencoder_model(cleaned, hidden_layer_sizes=(5, 2, 5), max_iter=100)
    anomalies = detect_ml_anomalies(
        cleaned,
        0.9,
        iso,
        dbscan_model=db_model,
        autoencoder_model=ae_model,
        dbscan_scaler=db_scaler,
        autoencoder_scaler=ae_scaler,
    )
    assert isinstance(anomalies, list)
