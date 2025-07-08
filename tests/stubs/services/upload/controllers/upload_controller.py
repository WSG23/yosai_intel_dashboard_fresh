class UnifiedUploadController:
    def __init__(self, callbacks=None):
        self.callbacks = callbacks

    def upload_callbacks(self):
        return []

    def progress_callbacks(self):
        return []

    def validation_callbacks(self):
        return []
