import boto3
from botocore.config import Config
from typing import Optional, BinaryIO
import uuid
from datetime import datetime
from app.core.config import settings


class StorageService:
    def __init__(self):
        self.use_r2 = settings.CLOUDFLARE_R2_ACCOUNT_ID is not None
        if self.use_r2:
            self.client = boto3.client(
                "s3",
                endpoint_url=settings.CLOUDFLARE_R2_ENDPOINT,
                aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
                aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
                config=Config(signature_version="s3v4"),
                region_name="auto",
            )
            self.bucket = settings.CLOUDFLARE_R2_BUCKET
        else:
            self.client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION,
                config=Config(signature_version="s3v4"),
            )
            self.bucket = settings.AWS_S3_BUCKET

    async def upload_file(
        self,
        file: BinaryIO,
        key: str,
        content_type: str = "video/mp4",
        metadata: Optional[dict] = None,
    ) -> str:
        extra_args = {"ContentType": content_type}
        if metadata:
            extra_args["Metadata"] = metadata

        self.client.upload_fileobj(file, self.bucket, key, ExtraArgs=extra_args)
        return key

    async def generate_presigned_url(
        self,
        key: str,
        expiration: int = 3600,
        method: str = "get_object",
    ) -> str:
        return self.client.generate_presigned_url(
            method,
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expiration,
        )

    async def generate_upload_url(
        self,
        filename: str,
        content_type: str = "video/mp4",
        expiration: int = 3600,
    ) -> tuple[str, str]:
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "mp4"
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        unique_id = str(uuid.uuid4())
        key = f"uploads/{date_prefix}/{unique_id}.{ext}"

        presigned_url = self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expiration,
        )
        return presigned_url, key

    async def delete_file(self, key: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    async def copy_file(self, source_key: str, dest_key: str) -> str:
        self.client.copy_object(
            Bucket=self.bucket,
            CopySource=f"{self.bucket}/{source_key}",
            Key=dest_key,
        )
        return dest_key


storage = StorageService()
