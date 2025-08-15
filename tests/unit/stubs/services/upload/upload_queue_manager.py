class UploadQueueManager:
    def __init__(self):
        self.files = []

    def add_file(self, name):
        self.files.append(name)

    def mark_complete(self, name):
        pass
