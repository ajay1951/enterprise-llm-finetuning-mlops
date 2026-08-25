from abc import ABC, abstractmethod
from typing import BinaryIO, Optional

class StorageInterface(ABC):
    @abstractmethod
    def save(self, path: str, content: BinaryIO) -> str:
        """Save content to storage and return the relative path/key."""
        pass

    @abstractmethod
    def read(self, path: str) -> BinaryIO:
        """Read content from storage."""
        pass

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Delete content from storage."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if content exists in storage."""
        pass
        
    @abstractmethod
    def get_metadata(self, path: str) -> dict:
        """Get file metadata like size and modified time."""
        pass
