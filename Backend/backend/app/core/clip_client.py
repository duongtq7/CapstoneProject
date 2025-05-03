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
        # Use the same endpoint as the keyframe extractor (pointing to Ray Serve)
        self.api_url = "http://10.12.0.11:8100/clip_image_encoder"
        self.timeout = 30.0  # seconds
        
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
            
            # Based on our investigation, the clip_api.py only supports URL-based embedding
            # So we'll only try the URL method and skip the others
            logger.info(f"Attempting embedding with URL: {image_url}")
            
            # Call the CLIP API with the image URL
            embedding_data = await self._try_url_embedding(image_url)
            
            if embedding_data is not None:
                logger.info(f"Successfully generated embedding with {len(embedding_data)} dimensions")
                # Flatten in case it's a 2D array with a single row
                if isinstance(embedding_data, list) and len(embedding_data) == 1 and isinstance(embedding_data[0], list):
                    embedding_data = embedding_data[0]
                    logger.info(f"Flattened embedding to {len(embedding_data)} dimensions")
                
                return embedding_data
            
            # URL method failed
            logger.error("URL embedding failed")
            return None
                
        except Exception as e:
            logger.error(f"Error calling CLIP API: {str(e)}")
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