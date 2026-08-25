import os
import hashlib
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
import json

from backend.forgellm_api.core.config import get_settings

settings = get_settings()

class ArtifactStorageError(Exception):
    pass

class ArtifactStorage:
    def upload(self, local_path: str, destination_uri: str) -> str:
        raise NotImplementedError

    def download(self, uri: str, local_path: str) -> str:
        raise NotImplementedError

    def exists(self, uri: str) -> bool:
        raise NotImplementedError

    def delete(self, uri: str):
        raise NotImplementedError

    def list(self, prefix: str) -> List[str]:
        raise NotImplementedError

    def checksum(self, local_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(local_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

class LocalStorage(ArtifactStorage):
    def __init__(self, base_dir: str = "/tmp/forgellm_storage"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_path(self, uri: str) -> str:
        # uri example: local://projects/project-123/models/v1/model.bin
        parsed = urlparse(uri)
        path = parsed.path.lstrip("/")
        return os.path.join(self.base_dir, path)

    def upload(self, local_path: str, destination_uri: str) -> str:
        import shutil
        dest = self._resolve_path(destination_uri)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(local_path, dest)
        return destination_uri

    def download(self, uri: str, local_path: str) -> str:
        import shutil
        src = self._resolve_path(uri)
        if not os.path.exists(src):
            raise ArtifactStorageError(f"File not found: {uri}")
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        shutil.copy2(src, local_path)
        return local_path

    def exists(self, uri: str) -> bool:
        return os.path.exists(self._resolve_path(uri))

    def delete(self, uri: str):
        path = self._resolve_path(uri)
        if os.path.exists(path):
            os.remove(path)

    def list(self, prefix: str) -> List[str]:
        # Simple mock list
        return []

class S3Storage(ArtifactStorage):
    def __init__(self):
        try:
            import boto3
            from botocore.client import Config
        except ImportError:
            raise ArtifactStorageError("boto3 is required for S3Storage")
            
        self.bucket = settings.STORAGE_BUCKET
        
        s3_kwargs = {}
        if hasattr(settings, 'S3_ENDPOINT_URL') and settings.S3_ENDPOINT_URL:
            s3_kwargs['endpoint_url'] = settings.S3_ENDPOINT_URL
            
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=getattr(settings, 'S3_ACCESS_KEY', 'minioadmin'),
            aws_secret_access_key=getattr(settings, 'S3_SECRET_KEY', 'minioadmin'),
            config=Config(signature_version='s3v4'),
            **s3_kwargs
        )

    def _get_key(self, uri: str) -> str:
        parsed = urlparse(uri)
        return parsed.path.lstrip("/")

    def upload(self, local_path: str, destination_uri: str) -> str:
        key = self._get_key(destination_uri)
        self.s3.upload_file(local_path, self.bucket, key)
        return destination_uri

    def download(self, uri: str, local_path: str) -> str:
        key = self._get_key(uri)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        self.s3.download_file(self.bucket, key, local_path)
        return local_path

    def exists(self, uri: str) -> bool:
        key = self._get_key(uri)
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except:
            return False

    def delete(self, uri: str):
        key = self._get_key(uri)
        self.s3.delete_object(Bucket=self.bucket, Key=key)

    def list(self, prefix: str) -> List[str]:
        key_prefix = self._get_key(prefix)
        paginator = self.s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket, Prefix=key_prefix)
        
        results = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    results.append(f"s3://{self.bucket}/{obj['Key']}")
        return results

def get_storage() -> ArtifactStorage:
    provider = getattr(settings, "STORAGE_PROVIDER", "local")
    if provider == "s3":
        return S3Storage()
    return LocalStorage()
