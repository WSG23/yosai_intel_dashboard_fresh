import re

with open('services/upload/protocols.py', 'r') as f:
    content = f.read()

missing_protocols = '''

@runtime_checkable
class UploadDataServiceProtocol(Protocol):
    """Protocol for upload data services."""
    
    @abstractmethod
    def get_upload_data(self) -> Dict[str, Any]: ...
    
    @abstractmethod
    def store_upload_data(self, data: Dict[str, Any]) -> bool: ...
    
    @abstractmethod
    def clear_data(self) -> None: ...

@runtime_checkable  
class DeviceLearningServiceProtocol(Protocol):
    """Protocol for device learning services."""
    
    @abstractmethod
    def get_user_device_mappings(self, filename: str) -> Dict[str, Any]: ...
    
    @abstractmethod
    def save_device_mappings(self, mappings: Dict[str, Any]) -> bool: ...
    
    @abstractmethod
    def learn_from_data(self, df: pd.DataFrame) -> Dict[str, Any]: ...

'''

content = content.rstrip() + missing_protocols

with open('services/upload/protocols.py', 'w') as f:
    f.write(content)

print("✅ Added missing protocols to services/upload/protocols.py")
