import httpx
import json
import base64
from typing import Optional
import uuid
import logging
import io

from app.core.config import settings
from app.core.object_storage import storage_manager

logger = logging.getLogger(__name__)

class ClipClient:
    """Client for interacting with the external CLIP API service."""
    
    def __init__(self):
        self.api_url = "http://localhost:8100/clip_image_encoder"
        self.timeout = 30.0  # seconds
        self.use_file_upload = False  # Default to False since we don't know if endpoint exists
        self._file_upload_checked = False
        
    async def _check_file_upload_endpoint(self):
        """Check if the file upload endpoint exists"""
        if self._file_upload_checked:
            return self.use_file_upload
            
        try:
            file_upload_url = self.api_url.replace("clip_image_encoder", "clip_image_file_encoder")
            async with httpx.AsyncClient(timeout=5.0) as client:  # Short timeout for just checking
                # Send an OPTIONS request to check if endpoint exists
                response = await client.options(file_upload_url)
                
                if response.status_code < 500:  # Any non-server error indicates endpoint likely exists
                    logger.info(f"File upload endpoint appears to exist: {file_upload_url}")
                    self.use_file_upload = True
                else:
                    logger.info(f"File upload endpoint does not appear to exist: {file_upload_url}")
                    self.use_file_upload = False
        except Exception as e:
            logger.info(f"Error checking file upload endpoint, assuming it doesn't exist: {str(e)}")
            self.use_file_upload = False
            
        self._file_upload_checked = True
        return self.use_file_upload
        
    async def get_image_embedding(self, image_url: str, object_key: str) -> Optional[list[float]]:
        """
        Get embedding for an image using the CLIP API.
        
        Args:
            image_url: URL of the image to embed
            object_key: Object storage key to directly access the file
            
        Returns:
            List of embedding values or None if the API call fails
        """
        try:
            logger.info(f"Starting embedding process for object: {object_key}")
            logger.info(f"CLIP API URL: {self.api_url}")
            
            # First try to get the image data directly from storage
            image_data = storage_manager.get_file_data(object_key)
            
            if not image_data:
                logger.error(f"Could not retrieve image data for {object_key}")
                return None
                
            logger.info(f"Successfully retrieved image data, size: {len(image_data)} bytes")
            
            # Try multiple approaches to get the embedding
            embedding_data = None
            
            # 1. Try with base64 encoded image
            logger.info("Starting base64 embedding attempt...")
            embedding_data = await self._try_base64_embedding(image_data)
            
            # 2. Try with multipart form upload if base64 failed
            if embedding_data is None and await self._check_file_upload_endpoint():
                logger.info("Base64 embedding failed, trying file upload...")
                embedding_data = await self._try_file_upload_embedding(image_data)
            elif embedding_data is None:
                logger.info("Skipping file upload attempt as endpoint not available")
            
            # 3. Try with URL if both previous methods failed
            if embedding_data is None:
                logger.info("Previous embedding methods failed, trying URL...")
                embedding_data = await self._try_url_embedding(image_url)
            
            if embedding_data is not None:
                logger.info(f"Successfully generated embedding with {len(embedding_data)} dimensions")
                # Flatten in case it's a 2D array with a single row
                if isinstance(embedding_data, list) and len(embedding_data) == 1 and isinstance(embedding_data[0], list):
                    embedding_data = embedding_data[0]
                    logger.info(f"Flattened embedding to {len(embedding_data)} dimensions")
                
                return embedding_data
            
            # All attempts failed
            logger.error("All embedding attempts failed")
            return None
                
        except Exception as e:
            logger.error(f"Error calling CLIP API: {str(e)}")
            return None
    
    async def _try_base64_embedding(self, image_data: bytes) -> Optional[list[float]]:
        """Try to get embedding using base64 encoded image"""
        try:
            # Encode the image data as base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "image_base64": base64_image,
                    "content_type": "image/jpeg"  # Adjust if needed
                }
                
                logger.info("Attempting embedding with base64 image")
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Base64 embedding failed: {response.status_code} - {response.text}")
                    return None
                
                return response.json()
        except Exception as e:
            logger.error(f"Error in base64 embedding: {str(e)}")
            return None
    
    async def _try_file_upload_embedding(self, image_data: bytes) -> Optional[list[float]]:
        """Try to get embedding using direct file upload"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info("Attempting embedding with file upload")
                
                files = {"file": ("image.jpg", image_data, "image/jpeg")}
                
                # Try a different endpoint that supports file upload
                file_upload_url = self.api_url.replace("clip_image_encoder", "clip_image_file_encoder")
                
                response = await client.post(
                    file_upload_url,
                    files=files,
                )
                
                if response.status_code != 200:
                    logger.error(f"File upload embedding failed: {response.status_code} - {response.text}")
                    return None
                
                return response.json()
        except Exception as e:
            logger.error(f"Error in file upload embedding: {str(e)}")
            return None
    
    async def _try_url_embedding(self, image_url: str) -> Optional[list[float]]:
        """Try to get embedding using image URL"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {"image_url": image_url}
                
                logger.info(f"Attempting embedding with URL: {image_url}")
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"URL embedding failed: {response.status_code} - {response.text}")
                    return None
                
                return response.json()
        except Exception as e:
            logger.error(f"Error in URL embedding: {str(e)}")
            return None

# Singleton instance
clip_client = ClipClient() 