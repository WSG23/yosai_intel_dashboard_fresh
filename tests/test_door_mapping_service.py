import pandas as pd
from services.door_mapping_service import DoorMappingService
from services.ai_device_generator import AIDeviceGenerator, DeviceAttributes

def test_standardized_output(monkeypatch):
    dummy = DeviceAttributes(
        device_id="d1",
        device_name="Door 1",
        floor_number=1,
        security_level=5,
        is_entry=True,
        is_exit=False,
        is_elevator=False,
        is_stairwell=False,
        is_fire_escape=False,
        confidence=0.9,
        ai_reasoning="test",
    )

    def fake_generate(self, device_id, *args, **kwargs):
        return dummy

    monkeypatch.setattr(AIDeviceGenerator, "generate_device_attributes", fake_generate)
    service = DoorMappingService()
    df = pd.DataFrame({"door_id": ["d1"]})
    result = service.process_uploaded_data(df)
    device = result["devices"][0]
    assert device["is_entry"] is True
    assert "entry" not in device

