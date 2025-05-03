import httpx
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class KeyframeExtractorClient:
    """Client for interacting with the KeyframeExtractor API service."""
    
    def __init__(self):
        self.api_url = "http://10.12.0.11:8100/key_frame_extractor"  # Existing Ray Serve endpoint
        self.timeout = 300.0  # 5 minutes timeout for video processing
        
    async def extract_keyframes(self, video_url: str, output_directory: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract keyframes from a video using the KeyframeExtractor API.
        
        Args:
            video_url: Path to the video file (accessible to the API service)
            output_directory: Optional directory to save keyframes to
            
        Returns:
            Dictionary with shot_boundaries and keyframes lists, or error status
        """
        try:
            logger.info(f"Starting keyframe extraction for video: {video_url}")
            logger.info(f"Using keyframe extractor endpoint: {self.api_url}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "video_path": video_url,
                    "output_directory": output_directory
                }
                
                logger.info(f"Sending request to keyframe extractor with payload: {payload}")
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Keyframe extraction failed: {response.status_code} - {response.text}")
                    # Return a default response with empty lists instead of failing
                    return {
                        "status": "error", 
                        "message": f"API error: {response.text}",
                        "keyframes": [],
                        "shot_boundaries": []
                    }
                
                result = response.json()
                logger.info(f"Keyframe extraction complete. Found {len(result.get('keyframes', []))} keyframes")
                
                # Ensure the result has the expected structure even if the API response is incomplete
                if not result.get("keyframes"):
                    result["keyframes"] = []
                if not result.get("shot_boundaries"):
                    result["shot_boundaries"] = []
                    
                return result
                
        except Exception as e:
            logger.error(f"Error calling KeyframeExtractor API: {str(e)}")
            # Return a default response with empty lists
            return {
                "status": "error", 
                "message": str(e),
                "keyframes": [],
                "shot_boundaries": []
            }

# Singleton instance
keyframe_client = KeyframeExtractorClient() 