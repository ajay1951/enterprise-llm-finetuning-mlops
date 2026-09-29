import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from backend.forgellm_api.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class S3StorageBackend(StorageBackend):
    """
    S3 Storage Backend compatible with AWS S3 and MinIO (for local dev).
    """

    def __init__(self):
        self.endpoint_url = os.environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
        self.access_key = os.environ.get("S3_ACCESS_KEY", "minioadmin")
        self.secret_key = os.environ.get("S3_SECRET_KEY", "minioadmin")
        self.bucket_name = os.environ.get("S3_BUCKET_NAME", "forgellm-models")

        # If running in production on AWS, these env vars might not be set,
        # so boto3 will fallback to IAM roles. For local dev, we point to MinIO.
        client_kwargs = {}
        if os.environ.get("USE_LOCAL_S3", "true").lower() == "true":
            client_kwargs = {
                "endpoint_url": self.endpoint_url,
                "aws_access_key_id": self.access_key,
                "aws_secret_access_key": self.secret_key,
            }

        self.s3_client = boto3.client("s3", **client_kwargs)
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created bucket {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to create bucket {self.bucket_name}: {e}")

    def upload_file(self, local_path: str, remote_path: str) -> str:
        """
        Uploads a local file to S3 and returns the s3:// URI.
        """
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, remote_path)
            return f"s3://{self.bucket_name}/{remote_path}"
        except Exception as e:
            logger.error(f"Failed to upload {local_path} to S3: {e}")
            raise

    def download_file(self, remote_path: str, local_path: str) -> str:
        """
        Downloads a file from S3 to a local path.
        """
        try:
            # Handle full s3:// URI or just the key
            key = remote_path.replace(f"s3://{self.bucket_name}/", "")
            self.s3_client.download_file(self.bucket_name, key, local_path)
            return local_path
        except Exception as e:
            logger.error(f"Failed to download {remote_path} from S3: {e}")
            raise
