class UploadValidator:
    def validate_file_upload(self, content):
        return type('Result', (), {'valid': True, 'message': ''})
