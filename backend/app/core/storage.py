import boto3
from botocore.config import Config
from typing import Optional, BinaryIO
import uuid
from datetime import datetime
from app.core.config import settings


class StorageService:
    def __init__(self):
        endpoint = settings.AWS_S3_ENDPOINT_URL
        if endpoint:
            self.client = boto3.client(
                "s3",
                endpoint_url=endpoint,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                config=Config(signature_version="s3v4"),
                region_name=settings.AWS_S3_REGION,
            )
        else:
            self.client = None
        self.bucket = settings.AWS_S3_BUCKET

    def _get_client(self):
        if not self.client:
            raise Exception("Storage not configured. Set AWS_S3_ENDPOINT_URL in env.")
        return self.client

    async def upload_file(self, file: BinaryIO, key: str, content_type: str = "video/mp4") -> str:
        client = self._get_client()
        client.upload_fileobj(file, self.bucket, key, ExtraArgs={"ContentType": content_type})
        return key

    async def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        client = self._get_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expiration,
        )

    async def generate_upload_url(self, filename: str, content_type: str = "video/mp4", expiration: int = 3600) -> tuple:
        client = self._get_client()
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "mp4"
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        key = f"uploads/{date_prefix}/{uuid.uuid4()}.{ext}"
        url = client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket, "Key": key, "ContentType": content_type},
            ExpiresIn=expiration,
        )
        return url, key

    async def delete_file(self, key: str) -> bool:
        try:
            client = self._get_client()
            client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    async def download_file(self, key: str, local_path: str) -> str:
        client = self._get_client()
        client.download_file(self.bucket, key, local_path)
        return local_path


storage = StorageService()
