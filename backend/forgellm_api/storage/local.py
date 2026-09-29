import os
import shutil
from typing import BinaryIO
from backend.forgellm_api.storage.base import StorageInterface


class LocalStorage(StorageInterface):
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        os.makedirs(self.root_dir, exist_ok=True)

    def _get_full_path(self, path: str) -> str:
        # Prevent directory traversal
        full_path = os.path.abspath(os.path.join(self.root_dir, path))
        if not full_path.startswith(self.root_dir):
            raise ValueError("Invalid path: Directory traversal detected")
        return full_path

    def save(self, path: str, content: BinaryIO) -> str:
        full_path = self._get_full_path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "wb") as f:
            shutil.copyfileobj(content, f)

        return path

    def read(self, path: str) -> BinaryIO:
        full_path = self._get_full_path(path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")
        return open(full_path, "rb")

    def delete(self, path: str) -> bool:
        full_path = self._get_full_path(path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    def exists(self, path: str) -> bool:
        full_path = self._get_full_path(path)
        return os.path.exists(full_path)

    def get_metadata(self, path: str) -> dict:
        full_path = self._get_full_path(path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")

        stats = os.stat(full_path)
        return {"size_bytes": stats.st_size, "modified_at": stats.st_mtime}
