import io
import os
import uuid
import logging
from typing import BinaryIO, Optional, List, Dict, Any
import cv2

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

    def save_keyframe(
        self,
        user_id: uuid.UUID,
        album_id: uuid.UUID, 
        video_key: str, 
        frame_idx: int,
        frame_data: bytes
    ) -> tuple[bool, str, str]:
        """
        Save a keyframe extracted from a video to object storage.
        
        Args:
            user_id: User ID
            album_id: Album ID
            video_key: Object key of the source video
            frame_idx: Frame index
            frame_data: Binary data of the frame image
            
        Returns:
            Tuple containing (success_status, url, object_key)
        """
        try:
            # Create an object key for the keyframe based on the video key
            video_name = os.path.splitext(os.path.basename(video_key))[0]
            
            # Format: users/{user_id}/albums/{album_id}/keyframes/{video_name}/frame_{idx}.jpg
            object_key = f"users/{user_id}/albums/{album_id}/keyframes/{video_name}/frame_{frame_idx}.jpg"
            
            # Upload the keyframe
            self.s3_client.upload_fileobj(
                io.BytesIO(frame_data),
                self.bucket_name,
                object_key,
                ExtraArgs={"ContentType": "image/jpeg"}
            )
            
            # Generate URL
            url = self.generate_presigned_url(object_key)
            
            return True, url, object_key
        except Exception as e:
            logger.error(f"Error saving keyframe: {str(e)}")
            return False, str(e), ""
            
    def extract_frame_from_video(
        self, 
        video_data: bytes, 
        frame_idx: int
    ) -> Optional[bytes]:
        """
        Extract a specific frame from video binary data.
        
        Args:
            video_data: Binary data of the video
            frame_idx: Index of the frame to extract
            
        Returns:
            Binary data of the extracted frame as JPEG, or None if extraction fails
        """
        try:
            # Save the video data to a temporary file
            temp_video_path = f"/tmp/{uuid.uuid4()}.mp4"
            with open(temp_video_path, "wb") as f:
                f.write(video_data)
            
            # Open the video
            cap = cv2.VideoCapture(temp_video_path)
            
            # Set the position to the desired frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            
            # Read the frame
            ret, frame = cap.read()
            if not ret:
                logger.error(f"Failed to read frame {frame_idx} from video")
                cap.release()
                os.remove(temp_video_path)
                return None
                
            # Convert to JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = buffer.tobytes()
            
            # Clean up
            cap.release()
            os.remove(temp_video_path)
            
            return frame_data
        except Exception as e:
            logger.error(f"Error extracting frame from video: {str(e)}")
            return None
            
    def process_keyframes_from_video(
        self,
        user_id: uuid.UUID,
        album_id: uuid.UUID,
        video_key: str,
        keyframe_indices: List[int]
    ) -> List[Dict[str, Any]]:
        """
        Process and save keyframes from a video.
        
        Args:
            user_id: User ID
            album_id: Album ID
            video_key: Object key of the source video
            keyframe_indices: List of frame indices to extract
            
        Returns:
            List of dictionaries with keyframe details (success, url, object_key, frame_idx)
        """
        results = []
        
        # Get video data
        video_data = self.get_file_data(video_key)
        if not video_data:
            logger.error(f"Failed to get video data for {video_key}")
            return results
            
        for frame_idx in keyframe_indices:
            # Extract the frame
            frame_data = self.extract_frame_from_video(video_data, frame_idx)
            if not frame_data:
                logger.error(f"Failed to extract frame {frame_idx} from video {video_key}")
                results.append({
                    "success": False,
                    "url": "",
                    "object_key": "",
                    "frame_idx": frame_idx,
                    "error": "Failed to extract frame"
                })
                continue
                
            # Save the frame to S3
            success, url, object_key = self.save_keyframe(
                user_id=user_id,
                album_id=album_id,
                video_key=video_key,
                frame_idx=frame_idx,
                frame_data=frame_data
            )
            
            results.append({
                "success": success,
                "url": url,
                "object_key": object_key,
                "frame_idx": frame_idx,
                "error": "" if success else "Failed to save keyframe"
            })
            
        return results


# Singleton instance
storage_manager = ObjectStorageManager()
