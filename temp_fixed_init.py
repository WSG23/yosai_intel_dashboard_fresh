    def __init__(self) -> None:
        # Initialize all preserved backend services
        self.upload_store = UploadedDataStore()
        self.file_processor = AsyncFileProcessor()
        self.validator = ClientSideValidator()
        
        # Add missing learning service
        from services.device_learning_service import DeviceLearningService
        self.learning_service = DeviceLearningService()
        
        self.processing_service = UploadProcessingService(
            store=self.upload_store,
            learning_service=self.learning_service,
            processor=self.file_processor,
            validator=self.validator,
        )

        # Initialize upload area with proper handler
        self.upload_area = UploadArea(
            upload_handler=self._handle_upload,
            upload_id="drag-drop-upload",
        )
