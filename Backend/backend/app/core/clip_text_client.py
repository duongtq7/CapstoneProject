import httpx
import logging
import time
from typing import Optional, List, Any
import json

logger = logging.getLogger(__name__)

class ClipTextClient:
    """Client for interacting with the external CLIP text encoder API."""
    
    def __init__(self):
        self.api_url = "http://localhost:8100/clip_text_encoder"
        self.timeout = 15.0  # Increased timeout
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        
    async def get_text_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for text using the CLIP API.
        
        Args:
            text: The text to embed
            
        Returns:
            List of embedding values or None if the API call fails
        """
        if not text or not text.strip():
            logger.error("Empty text provided for embedding")
            return None
            
        attempts = 0
        last_error = None
        
        while attempts < self.max_retries:
            attempts += 1
            try:
                logger.info(f"Attempt {attempts}: Generating text embedding for text: '{text[:50]}...' (truncated)")
                
                # Create the payload
                payload = {"text": text}
                logger.info(f"Sending request to CLIP text encoder API: {self.api_url}")
                
                # Log the detailed request information
                logger.info(f"Request payload: {json.dumps(payload)}")
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.api_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    status_code = response.status_code
                    logger.info(f"Response status code: {status_code}")
                    
                    if status_code != 200:
                        error_message = f"Text embedding failed: {status_code} - {response.text}"
                        logger.error(error_message)
                        last_error = error_message
                        if status_code >= 500:  # Server errors, worth retrying
                            if attempts < self.max_retries:
                                logger.info(f"Will retry in {self.retry_delay} seconds")
                                time.sleep(self.retry_delay)
                                continue
                        return None
                    
                    # Try to parse the JSON response
                    try:
                        embedding_data = response.json()
                    except Exception as e:
                        logger.error(f"Failed to parse JSON response: {str(e)}")
                        logger.error(f"Response content: {response.text[:200]}...")
                        last_error = f"Invalid JSON response: {str(e)}"
                        if attempts < self.max_retries:
                            time.sleep(self.retry_delay)
                            continue
                        return None
                    
                    # Check if we got a valid embedding
                    if not embedding_data or not isinstance(embedding_data, list):
                        logger.error(f"Invalid embedding data received: {type(embedding_data)}")
                        logger.error(f"Response content: {str(embedding_data)[:200]}...")
                        last_error = "Invalid embedding data format"
                        if attempts < self.max_retries:
                            time.sleep(self.retry_delay)
                            continue
                        return None
                    
                    # Flatten in case it's a 2D array with a single row
                    if isinstance(embedding_data, list) and len(embedding_data) > 0 and isinstance(embedding_data[0], list):
                        embedding_data = embedding_data[0]
                        logger.info(f"Flattened embedding to {len(embedding_data)} dimensions")
                    
                    # Verify embedding dimensions
                    if len(embedding_data) != 512:
                        logger.warning(f"Unexpected embedding dimensions: {len(embedding_data)} (expected 512)")
                    
                    logger.info(f"Successfully generated text embedding with {len(embedding_data)} dimensions")
                    return embedding_data
                    
            except Exception as e:
                logger.error(f"Error calling CLIP text API: {str(e)}")
                last_error = str(e)
                if attempts < self.max_retries:
                    logger.info(f"Will retry in {self.retry_delay} seconds")
                    time.sleep(self.retry_delay)
                    continue
        
        logger.error(f"Failed to get text embedding after {self.max_retries} attempts. Last error: {last_error}")
        return None

# Singleton instance
clip_text_client = ClipTextClient() 