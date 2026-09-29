import os
import shutil
from typing import Optional


class ArtifactCacheManager:
    def __init__(
        self, cache_dir: str = "/tmp/forgellm_cache", max_size_gb: float = 200.0
    ):
        self.cache_dir = cache_dir
        self.max_size_gb = max_size_gb
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_path(self, uri: str) -> str:
        # e.g., s3://forgellm/projects/1/models/abc -> <cache_dir>/models/abc
        safe_name = uri.replace("://", "_").replace("/", "_")
        return os.path.join(self.cache_dir, safe_name)

    def _get_current_size_gb(self) -> float:
        total = 0
        for dirpath, _, filenames in os.walk(self.cache_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total += os.path.getsize(fp)
        return total / (1024**3)

    def _evict_lru(self, required_gb: float = 0.0):
        current_size = self._get_current_size_gb()
        if current_size + required_gb <= self.max_size_gb:
            return

        # Get all files sorted by access time (oldest first)
        files = []
        for dirpath, _, filenames in os.walk(self.cache_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                stat = os.stat(fp)
                files.append((fp, stat.st_atime, stat.st_size))

        files.sort(key=lambda x: x[1])

        freed = 0
        for fp, _, size in files:
            if current_size + required_gb - freed <= self.max_size_gb:
                break
            try:
                os.remove(fp)
                freed += size / (1024**3)
                print(f"Cache Eviction: Removed {fp}")
            except:
                pass

    async def get_artifact(self, uri: str, required_gb: float = 0.0) -> str:
        """
        Returns local path to the artifact, downloading it if not present.
        """
        path = self._get_cache_path(uri)
        if os.path.exists(path):
            # Update access time
            os.utime(path, None)
            return path

        self._evict_lru(required_gb)

        # Download logic would go here (using httpx to hit control plane API or S3 directly)
        print(f"Downloading artifact {uri} to {path}...")

        # Mock download for now
        with open(path, "w") as f:
            f.write("mock content")

        return path
