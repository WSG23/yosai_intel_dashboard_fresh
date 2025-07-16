import re

# Add the missing UploadDataServiceProtocol to services/interfaces.py
print("Adding missing UploadDataServiceProtocol...")
with open("services/interfaces.py", "r") as f:
    content = f.read()

# Add the missing protocol after the existing ones
missing_protocol = '''

@runtime_checkable
class UploadDataServiceProtocol(Protocol):
    """Interface for upload data services."""
    
    def get_upload_data(self) -> Dict[str, Any]: ...
    def store_upload_data(self, data: Dict[str, Any]) -> bool: ...
    def clear_data(self) -> None: ...

@runtime_checkable  
class DeviceLearningServiceProtocol(Protocol):
    """Interface for device learning services."""
    
    def get_user_device_mappings(self, filename: str) -> Dict[str, Any]: ...
    def save_device_mappings(self, mappings: Dict[str, Any]) -> bool: ...
    def learn_from_data(self, df: pd.DataFrame) -> Dict[str, Any]: ...

'''

# Insert before the end of the file
content = content.rstrip() + missing_protocol

with open("services/interfaces.py", "w") as f:
    f.write(content)

print("✅ Added missing protocols to services/interfaces.py")
