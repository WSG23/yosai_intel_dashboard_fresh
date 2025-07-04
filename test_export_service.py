import unittest
from io import StringIO
import pandas as pd
import importlib.util
import sys
import types

# Create stub modules to satisfy dependencies when loading export_service
consolidated_stub = types.ModuleType("services.consolidated_learning_service")
consolidated_stub.get_learning_service = lambda: None
device_stub = types.ModuleType("services.device_learning_service")
device_stub.get_device_learning_service = lambda: None
sys.modules["services.consolidated_learning_service"] = consolidated_stub
sys.modules["services.device_learning_service"] = device_stub

spec = importlib.util.spec_from_file_location(
    "export_service", "services/export_service.py"
)
export_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export_service)

class ExportServiceCsvTest(unittest.TestCase):
    def test_rows_per_device(self):
        data = {
            "abc": {
                "filename": "file.csv",
                "saved_at": "2024-01-01T00:00:00",
                "source": "user_confirmed",
                "device_count": 2,
                "device_mappings": {
                    "door1": {"floor_number": 1, "security_level": 2},
                    "door2": {"floor_number": 2, "security_level": 3},
                },
            }
        }
        csv = export_service.to_csv_string(data)
        df = pd.read_csv(StringIO(csv))
        self.assertEqual(len(df), 2)
        self.assertSetEqual(set(df["device_name"]), {"door1", "door2"})

    def test_legacy_mappings(self):
        data = {
            "def": {
                "filename": "legacy.csv",
                "learned_at": "2024-01-02T00:00:00",
                "source": "legacy",
                "device_count": 1,
                "mappings": {"dev": {"floor_number": 3, "security_level": 1}},
            }
        }
        csv = export_service.to_csv_string(data)
        df = pd.read_csv(StringIO(csv))
        self.assertEqual(len(df), 1)
        self.assertEqual(df.loc[0, "device_name"], "dev")
        self.assertEqual(df.loc[0, "floor_number"], 3)

if __name__ == "__main__":
    unittest.main()
