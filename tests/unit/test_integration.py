"""Integration tests for modular AI components."""

import pandas as pd

from yosai_intel_dashboard.src.services.ai_device_generator import AIDeviceGenerator
from yosai_intel_dashboard.src.services.learning.src.api.consolidated_service import get_learning_service


def test_end_to_end_device_mapping():
    generator = AIDeviceGenerator()
    attrs = generator.generate_device_attributes("office_3F_entrance")
    assert attrs.floor_number == 3
    assert attrs.is_entry is True

    df = pd.DataFrame({"door_id": [attrs.device_id]})
    device_mappings = {attrs.device_id: attrs.__dict__}
    learning_service = get_learning_service()
    fingerprint = learning_service.save_complete_mapping(
        df, "test.csv", device_mappings
    )

    learned = learning_service.get_learned_mappings(df, "test.csv")
    assert learned["match_type"] == "exact"
    assert attrs.device_id in learned["device_mappings"]


def test_ai_generator_with_learning_service():
    generator = AIDeviceGenerator()
    learning_service = get_learning_service()

    devices = ["lobby_L1", "office_2F_door", "server_room_3F"]
    all_mappings = {}
    for device in devices:
        attrs = generator.generate_device_attributes(device)
        all_mappings[device] = {
            "floor_number": attrs.floor_number,
            "security_level": attrs.security_level,
            "device_name": attrs.device_name,
        }

    df = pd.DataFrame({"door_id": devices})
    fingerprint = learning_service.save_complete_mapping(
        df, "multi_device.csv", all_mappings
    )
    learned = learning_service.get_learned_mappings(df, "multi_device.csv")
    assert len(learned["device_mappings"]) == 3
    assert learned["confidence"] == 1.0
