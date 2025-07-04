import unittest
from io import StringIO
import pandas as pd
import importlib.util
import sys
import types

class DummyLearningService:
    def __init__(self):
        self.learned_data = {}
    def _persist_learned_data(self):
        pass

def stub_get_learning_service():
    return DummyLearningService()

class DummyDeviceService:
    def __init__(self):
        self.learned_mappings = {}

def stub_get_device_learning_service():
    return DummyDeviceService()

# Stub required modules before loading export_service
consolidated_stub = types.ModuleType("services.consolidated_learning_service")
consolidated_stub.get_learning_service = stub_get_learning_service
device_stub = types.ModuleType("services.device_learning_service")
device_stub.get_device_learning_service = stub_get_device_learning_service
sys.modules["services.consolidated_learning_service"] = consolidated_stub
sys.modules["services.device_learning_service"] = device_stub

spec = importlib.util.spec_from_file_location("export_service", "services/export_service.py")
export_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export_service)


class ExportServiceCsvTest(unittest.TestCase):
    def test_wide_csv_structure(self):
        data = {
            "abc": {
                "filename": "file.csv",
                "saved_at": "2024-01-01T00:00:00",
                "source": "user_confirmed",
                "device_count": 2,
                "device_mappings": {
                    "door1": {"floor": 1, "sec": 2},
                    "door2": {"floor": 2, "sec": 3},
                },
                "column_mappings": {"uid": "user_id"},
            }
        }
        csv = export_service.to_csv_string(data)
        df = pd.read_csv(StringIO(csv))
        self.assertEqual(len(df), 1)
        self.assertIn("mappings.door1.floor", df.columns)
        self.assertEqual(df.loc[0, "mappings.door2.sec"], 3)
        self.assertEqual(df.loc[0, "column_mappings.uid"], "user_id")

    def test_empty_export(self):
        csv = export_service.to_csv_string({})
        self.assertEqual(csv, "")


if __name__ == "__main__":
    unittest.main()
