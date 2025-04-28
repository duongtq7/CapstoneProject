import io
import os
import uuid
import logging
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)

class ObjectStorageManager:
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_INTERNAL_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=boto3.session.Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Ensure that the bucket exists, creating it if necessary."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            # The bucket does not exist or you have no access.
            if e.response["Error"]["Code"] == "404":
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                # Handle other errors
                print(f"Error checking bucket: {e}")

    def generate_media_key(
        self, user_id: uuid.UUID, album_id: uuid.UUID, filename: str
    ) -> str:
        """Generate a key for storing a media file."""
        _, ext = os.path.splitext(filename)
        return f"users/{user_id}/albums/{album_id}/{uuid.uuid4()}{ext}"

    async def upload_file(
        self,
        user_id: uuid.UUID,
        album_id: uuid.UUID,
        file: UploadFile,
        metadata: dict[str, str] | None = None,
    ) -> tuple[bool, str, str]:
        """Upload a file to object storage.

        Returns:
            Tuple containing (success_status, url, object_key)
        """
        try:
            object_key = self.generate_media_key(user_id, album_id, file.filename)

            # Read the content of the file
            content = await file.read()

            # Upload the file to MinIO
            self.s3_client.upload_fileobj(
                io.BytesIO(content),
                self.bucket_name,
                object_key,
                ExtraArgs={"Metadata": metadata} if metadata else {},
            )

            # Reset the position in the file to the beginning
            await file.seek(0)

            # Generate and return the public URL for the uploaded file
            url = self.generate_presigned_url(object_key)

            return True, url, object_key
        except Exception as e:
            print(f"Error uploading file: {e}")
            return False, str(e), ""

    def upload_bytes(
        self,
        user_id: uuid.UUID,
        album_id: uuid.UUID,
        bytes_data: BinaryIO,
        filename: str,
        metadata: dict[str, str] | None = None,
    ) -> tuple[bool, str, str]:
        """Upload bytes to object storage.

        Returns:
            Tuple containing (success_status, url, object_key)
        """
        try:
            object_key = self.generate_media_key(user_id, album_id, filename)

            # Upload the bytes to MinIO
            self.s3_client.upload_fileobj(
                bytes_data,
                self.bucket_name,
                object_key,
                ExtraArgs={"Metadata": metadata} if metadata else {},
            )

            # Generate and return the public URL for the uploaded file
            url = self.generate_presigned_url(object_key)

            return True, url, object_key
        except Exception as e:
            print(f"Error uploading bytes: {e}")
            return False, str(e), ""

    def delete_file(self, object_key: str) -> bool:
        """Delete a file from object storage."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    def get_file_data(self, object_key: str) -> bytes | None:
        """Get file data from object storage."""
        try:
            logger.info(f"Getting file data for {object_key}")
            logger.info(f"Bucket: {self.bucket_name}")
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=object_key,
            )
            # Read the binary data from the response
            data = response["Body"].read()
            
            logger.info(f"Successfully retrieved file data: {len(data)} bytes")
            content_type = response.get("ContentType", "unknown")
            logger.info(f"Content type: {content_type}")
            
            return data
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            logger.error(f"S3 client error getting file data: Code {error_code} - {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting file data: {str(e)}")
            return None

    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for accessing a file."""
        try:
            # Create a new client with the external URL for generating presigned URLs
            external_client = boto3.client(
                "s3",
                endpoint_url=f"http{'s' if settings.S3_REQUIRE_TLS else ''}://{settings.S3_EXTERNAL_HOST}",
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
                region_name=settings.S3_REGION,
                config=boto3.session.Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path"},
                ),
            )

            url = external_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expiration,
            )
            return url
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return ""


# Singleton instance
storage_manager = ObjectStorageManager()
