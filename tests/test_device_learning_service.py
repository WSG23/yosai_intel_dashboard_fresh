import json

import pandas as pd

from yosai_intel_dashboard.src.services.device_learning_service import DeviceLearningService


def _init_service(tmp_path):
    svc = DeviceLearningService()
    svc.storage_dir = tmp_path
    svc.learned_mappings = {}
    svc.storage_dir.mkdir(parents=True, exist_ok=True)
    return svc


def test_save_and_load_user_mappings(tmp_path):
    df = pd.DataFrame({"door_id": ["d1", "d2"]})
    mappings = {
        "d1": {
            "floor_number": 1,
            "security_level": 2,
            "device_name": "d1",
            "is_entry": True,
            "is_exit": False,
        },
        "d2": {
            "floor_number": 2,
            "security_level": 3,
            "device_name": "d2",
            "is_entry": False,
            "is_exit": True,
        },
    }
    svc = _init_service(tmp_path)
    assert svc.save_user_device_mappings(df, "test.csv", mappings) is True
    files = list(tmp_path.glob("mapping_*.json"))
    assert len(files) == 1
    # verify file structure
    with open(files[0], "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert "device_mappings" in data
    # simulate restart
    new_svc = _init_service(tmp_path)
    new_svc._load_all_learned_mappings()
    loaded = new_svc.get_user_device_mappings("test.csv")
    assert loaded == mappings


def test_load_legacy_mappings(tmp_path):
    legacy_mapping = {
        "filename": "legacy.csv",
        "fingerprint": "abcd",
        "source": "user_confirmed",
        "device_count": 1,
        "mappings": {"d1": {"floor": 1}},
    }
    tmp_path.mkdir(parents=True, exist_ok=True)
    file_path = tmp_path / "mapping_abcd.json"
    with open(file_path, "w", encoding="utf-8") as fh:
        json.dump(legacy_mapping, fh)
    svc = _init_service(tmp_path)
    svc._load_all_learned_mappings()
    loaded = svc.get_user_device_mappings("legacy.csv")
    assert loaded == legacy_mapping["mappings"]
