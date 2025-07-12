from core.callback_events import CallbackEvent
from core.callback_manager import CallbackManager

UIEvent = CallbackEvent
UICallbackController = CallbackManager
ui_callback_controller = CallbackManager()

__all__ = ["UIEvent", "UICallbackController", "ui_callback_controller"]
