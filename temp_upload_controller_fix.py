# Look at the current controller and see what's None
import inspect
from services.upload.controllers.upload_controller import UnifiedUploadController

controller = UnifiedUploadController()
print("=== CONTROLLER SOURCE ===")
print(inspect.getsource(controller.upload_callbacks))
