"""
Test file for callback controller functionality
Save as: tests/test_callback_controller.py
"""

import threading
import time
from datetime import datetime

import pytest

from core.callback_events import CallbackEvent
from core.callback_manager import CallbackManager


class CallbackContext:
    def __init__(self, event_type, source_id, data=None):
        self.event_type = event_type
        self.source_id = source_id
        self.data = data or {}


class CallbackController(CallbackManager):
    def fire_event(self, event: CallbackEvent, source_id: str, data=None):
        ctx = CallbackContext(event, source_id, data)
        self.trigger(event, ctx)


def callback_handler(event: CallbackEvent):
    def decorator(func):
        _GLOBAL.register_callback(event, func)
        return func
    return decorator


class TemporaryCallback:
    def __init__(self, event: CallbackEvent, cb, controller: CallbackController):
        self.event = event
        self.cb = cb
        self.controller = controller

    def __enter__(self):
        self.controller.register_callback(self.event, self.cb)
        return self.cb

    def __exit__(self, exc_type, exc, tb):
        self.controller.unregister_callback(self.event, self.cb)


_GLOBAL = CallbackController()
fire_event = _GLOBAL.fire_event



class TestCallbackController:
    """Test the callback controller functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.controller = CallbackController()
        self.controller._callbacks.clear()
    
    def test_callback_registration(self):
        """Test basic callback registration"""
        callback_executed = []
        
        def test_callback(context):
            callback_executed.append(context)
        
        self.controller.register_callback(CallbackEvent.FILE_PROCESSING_START, test_callback)
        
        self.controller.fire_event(
            CallbackEvent.FILE_PROCESSING_START,
            "test_source",
            {"filename": "test.csv"}
        )
        
        assert len(callback_executed) == 1
    
    def test_multiple_callbacks(self):
        """Test multiple callbacks for same event"""
        results = []
        
        def callback1(context):
            results.append("callback1")
        
        def callback2(context):
            results.append("callback2")
        
        event = CallbackEvent.ANALYSIS_START
        self.controller.register_callback(event, callback1)
        self.controller.register_callback(event, callback2)
        self.controller.fire_event(event, "test", {})
        
        assert "callback1" in results
        assert "callback2" in results
    
    def test_callback_error_handling(self):
        """Test error handling in callbacks"""
        working_callback_executed = []
        
        def failing_callback(context):
            raise ValueError("Test error")
        
        def working_callback(context):
            working_callback_executed.append("worked")
        
        event = CallbackEvent.FILE_PROCESSING_START
        self.controller.register_callback(event, failing_callback)
        self.controller.register_callback(event, working_callback)
        self.controller.fire_event(event, "test", {})

        assert "worked" in working_callback_executed
    
    def test_callback_unregistration(self):
        """Test callback removal"""
        executed = []
        
        def test_callback(context):
            executed.append("executed")
        
        event = CallbackEvent.FILE_PROCESSING_START

        self.controller.register_callback(event, test_callback)
        self.controller.fire_event(event, "test", {})

        self.controller.unregister_callback(event, test_callback)
        self.controller.fire_event(event, "test", {})

        assert len(executed) == 1
