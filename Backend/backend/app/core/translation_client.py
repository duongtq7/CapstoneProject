import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

class TranslationClient:
    """Client for Vietnamese to English translation API."""
    
    def __init__(self, translation_api_url: str = "http://localhost:8100"):
        self.translation_api_url = translation_api_url
        logger.info(f"Initialized translation client with API URL: {translation_api_url}")
    
    async def translate_vi_to_en(self, text: str) -> Optional[str]:
        """
        Translate text from Vietnamese to English.
        
        Args:
            text: The Vietnamese text to translate
            
        Returns:
            The translated English text or None if translation failed
        """
        if not text:
            logger.warning("Empty text provided for translation")
            return text
            
        try:
            logger.info(f"Translating text: '{text}'")
            
            # Prepare the request payload
            payload = {"text": text}
            
            # Make the translation request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.translation_api_url}/vi2en",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                
                # Extract the translated text from the response format
                # The API returns {"original": "...", "translated": ["..."]}
                translated_list = result.get("translated", [])
                
                if translated_list and isinstance(translated_list, list) and len(translated_list) > 0:
                    translated_text = translated_list[0]
                    logger.info(f"Translation successful: '{text}' -> '{translated_text}'")
                    return translated_text
                else:
                    logger.warning(f"Translation response has unexpected format: {result}")
                    return text
            else:
                logger.error(f"Translation API error: {response.status_code} - {response.text}")
                # Return original text on error
                return text
                
        except Exception as e:
            logger.exception(f"Error translating text: {str(e)}")
            # Return original text on error
            return text

# Create a singleton instance
translation_client = TranslationClient() 