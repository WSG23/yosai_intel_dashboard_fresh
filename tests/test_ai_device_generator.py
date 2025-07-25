"""
Test suite for AI device generator module.
"""

import pytest

from yosai_intel_dashboard.src.services.ai_device_generator import AIDeviceGenerator, DeviceAttributes


class TestAIDeviceGenerator:

    def setup_method(self):
        """Setup test instance."""
        self.generator = AIDeviceGenerator()

    def test_floor_extraction_patterns(self):
        """Test floor number extraction from various patterns."""
        test_cases = [
            ("lobby_L1_door", 1),
            ("office_3F_main", 3),
            ("floor_2_entrance", 2),
            ("5_server_room", 5),
            ("basement_door", 1),  # default
            ("office_201_door", 1),  # default with new logic
            ("device_F01A", 1),  # new F01A pattern
            ("device_F12B", 12),  # higher floor with F12B format
        ]

        for device_id, expected_floor in test_cases:
            attrs = self.generator.generate_device_attributes(device_id)
            assert (
                attrs.floor_number == expected_floor
            ), f"Failed for {device_id}: got {attrs.floor_number}, expected {expected_floor}"

    def test_security_level_detection(self):
        """Test security level assignment."""
        test_cases = [
            ("lobby_entrance", 4),  # entrance pattern
            ("office", 5),  # office default pattern
            ("server_room_door", 9),  # server room
            ("executive_suite", 6),  # executive pattern
            ("elevator_1", 3),  # elevator
            ("vault_door", 5),  # no specific match -> default
        ]

        for device_id, expected_security in test_cases:
            attrs = self.generator.generate_device_attributes(device_id)
            assert (
                attrs.security_level == expected_security
            ), f"Failed for {device_id}: got {attrs.security_level}, expected {expected_security}"

    def test_access_type_detection(self):
        """Test access type flag detection."""
        test_cases = [
            ("main_entrance", True, False, False),  # entry, not exit, not elevator
            ("emergency_exit", False, True, False),  # exit, not entry
            ("elevator_1", False, False, True),  # elevator
            ("fire_escape", False, True, False),  # fire escape (counts as exit)
        ]

        for device_id, expect_entry, expect_exit, expect_elevator in test_cases:
            attrs = self.generator.generate_device_attributes(device_id)
            assert (
                attrs.is_entry == expect_entry
            ), f"Entry failed for {device_id}: got {attrs.is_entry}, expected {expect_entry}"
            assert (
                attrs.is_exit == expect_exit
            ), f"Exit failed for {device_id}: got {attrs.is_exit}, expected {expect_exit}"
            assert (
                attrs.is_elevator == expect_elevator
            ), f"Elevator failed for {device_id}: got {attrs.is_elevator}, expected {expect_elevator}"

    def test_device_name_generation(self):
        """Test readable name generation."""
        test_cases = [
            ("lobby_L1_door", "Lobby L 1 Door"),  # Updated formatting
            ("office_201", "Office 201"),  # Keep room numbers together
            ("server-room_3F", "Server Room 3F"),  # Handle both separators
            ("device_F01A", "Floor 1 Wing A"),  # New location format
        ]

        for device_id, expected_name in test_cases:
            attrs = self.generator.generate_device_attributes(device_id)
            assert (
                attrs.device_name == expected_name
            ), f"Name failed for {device_id}: got '{attrs.device_name}', expected '{expected_name}'"

    def test_confidence_calculation(self):
        """Test confidence scoring."""
        # Device with clear patterns should have higher confidence
        clear_attrs = self.generator.generate_device_attributes("office_3F_entrance")
        unclear_attrs = self.generator.generate_device_attributes("device_123")

        assert (
            clear_attrs.confidence > unclear_attrs.confidence
        ), f"Clear confidence {clear_attrs.confidence} should be > unclear confidence {unclear_attrs.confidence}"
        assert 0.3 <= clear_attrs.confidence <= 0.95
        assert 0.3 <= unclear_attrs.confidence <= 0.95

    def test_ai_reasoning_output(self):
        """Test that AI reasoning is populated."""
        attrs = self.generator.generate_device_attributes("office_2F_door")

        assert attrs.ai_reasoning is not None
        assert len(attrs.ai_reasoning) > 0
        assert "Floor" in attrs.ai_reasoning or "Security" in attrs.ai_reasoning

    def test_fire_escape_is_exit(self):
        """Test that fire escapes are marked as exits."""
        attrs = self.generator.generate_device_attributes("fire_escape_door")

        assert attrs.is_fire_escape == True
        assert attrs.is_exit == True  # Fire escapes should also be exits
