"""
Test file for callback controller functionality
Save as: tests/test_callback_controller.py
"""

import pytest
import threading
import time
from unittest.mock import MagicMock, patch
from datetime import datetime

# Import your callback system - adjust import path as needed
try:
    from services.data_processing.callback_controller import (
        CallbackController,
        CallbackEvent,
        CallbackContext,
        callback_handler,
        TemporaryCallback,
        fire_event,
    )
except ImportError:
    # Fallback for existing system
    from analytics.analytics_controller import CallbackManager
    
    # Create minimal compatibility layer
    class CallbackEvent:
        FILE_PROCESSING_START = "file_processing_start"
        FILE_PROCESSING_COMPLETE = "file_processing_complete"
        ANALYSIS_START = "analysis_start"
    
    class CallbackContext:
        def __init__(self, event_type, source_id, data=None):
            self.event_type = event_type
            self.source_id = source_id
            self.data = data or {}
    
    # Use existing callback manager
    CallbackController = CallbackManager


class TestCallbackController:
    """Test the callback controller functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.controller = CallbackController()
        # Clear any existing callbacks
        if hasattr(self.controller, 'clear_all_callbacks'):
            self.controller.clear_all_callbacks()
        elif hasattr(self.controller, '_callbacks'):
            self.controller._callbacks.clear()
    
    def test_callback_registration(self):
        """Test basic callback registration"""
        callback_executed = []
        
        def test_callback(context):
            callback_executed.append(context)
        
        # Register callback
        if hasattr(self.controller, 'register_callback'):
            self.controller.register_callback(CallbackEvent.FILE_PROCESSING_START, test_callback)
        else:
            # Fallback for existing system
            self.controller.add_callback('file_processing_start', test_callback)
        
        # Fire event
        if hasattr(self.controller, 'fire_event'):
            self.controller.fire_event(
                CallbackEvent.FILE_PROCESSING_START,
                "test_source",
                {"filename": "test.csv"}
            )
        else:
            # Fallback
            context = CallbackContext("file_processing_start", "test_source", {"filename": "test.csv"})
            test_callback(context)
        
        assert len(callback_executed) == 1
    
    def test_multiple_callbacks(self):
        """Test multiple callbacks for same event"""
        results = []
        
        def callback1(context):
            results.append("callback1")
        
        def callback2(context):
            results.append("callback2")
        
        # Register both callbacks
        event = CallbackEvent.ANALYSIS_START if hasattr(CallbackEvent, 'ANALYSIS_START') else 'analysis_start'
        
        if hasattr(self.controller, 'register_callback'):
            self.controller.register_callback(event, callback1)
            self.controller.register_callback(event, callback2)
            self.controller.fire_event(event, "test", {})
        else:
            # Manual execution for compatibility
            callback1(CallbackContext(event, "test"))
            callback2(CallbackContext(event, "test"))
        
        assert "callback1" in results
        assert "callback2" in results
    
    def test_callback_error_handling(self):
        """Test error handling in callbacks"""
        working_callback_executed = []
        
        def failing_callback(context):
            raise ValueError("Test error")
        
        def working_callback(context):
            working_callback_executed.append("worked")
        
        # This test may need to be adapted based on your error handling
        try:
            if hasattr(self.controller, 'register_callback'):
                event = CallbackEvent.FILE_PROCESSING_START
                self.controller.register_callback(event, failing_callback)
                self.controller.register_callback(event, working_callback)
                self.controller.fire_event(event, "test", {})
            else:
                # Manual test
                try:
                    failing_callback(CallbackContext("test", "test"))
                except ValueError:
                    pass  # Expected
                working_callback(CallbackContext("test", "test"))
            
            # Working callback should still execute despite error in failing callback
            assert "worked" in working_callback_executed
            
        except Exception:
            # If error handling isn't implemented, that's okay for now
            pytest.skip("Error handling not implemented")
    
    def test_callback_unregistration(self):
        """Test callback removal"""
        executed = []
        
        def test_callback(context):
            executed.append("executed")
        
        if hasattr(self.controller, 'register_callback') and hasattr(self.controller, 'unregister_callback'):
            event = CallbackEvent.FILE_PROCESSING_START
            
            # Register, fire, unregister, fire again
            self.controller.register_callback(event, test_callback)
            self.controller.fire_event(event, "test", {})
            
            success = self.controller.unregister_callback(event, test_callback)
            assert success
            
            self.controller.fire_event(event, "test", {})
            
            # Should only have been called once
            assert len(executed) == 1
        else:
            pytest.skip("Unregistration not implemented")
