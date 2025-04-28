import uuid
import logging
import time
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session

from app import crud
from app.api.deps import get_current_user, get_db
from app.core.vector_db import qdrant_manager
from app.core.object_storage import storage_manager
from app.core.clip_text_client import clip_text_client  # Import the text client
from app.models.media import MediaResponse
from app.models.user import User

router = APIRouter()

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """Model for search results with score and media data."""
    media: MediaResponse
    score: float


class SearchResponse(BaseModel):
    """Model for the search endpoint response."""
    results: List[SearchResult]
    count: int


@router.get("/", response_model=SearchResponse)
async def search_media(
    *,
    db: Session = Depends(get_db),
    query: str = Query(..., min_length=1, description="Search query text"),
    limit: int = Query(5, ge=1, le=100, description="Maximum number of results to return"),
    debug: bool = Query(False, description="Include debug information in the response"),
    current_user: User = Depends(get_current_user),
) -> SearchResponse:
    """
    Search for media using semantic text search.
    Uses CLIP to convert text to embeddings and finds similar media in Qdrant.
    """
    logger.info(f"Starting search with query: '{query}' for user: {current_user.id}")
    
    start_time = time.time()
    
    # Get the text embedding from CLIP API
    text_embedding = await clip_text_client.get_text_embedding(query)
    
    embedding_time = time.time() - start_time
    logger.info(f"Text embedding generation took {embedding_time:.2f} seconds")
    
    if not text_embedding:
        logger.error("Failed to generate text embedding")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate text embedding",
        )
    
    logger.info(f"Successfully generated text embedding with {len(text_embedding)} dimensions")
    
    # Create filter to only search user's media
    filter_params = {
        "user_id": str(current_user.id)
    }
    
    logger.info(f"Searching Qdrant with filter: {filter_params}")
    
    search_start_time = time.time()
    
    # Search Qdrant using the text embedding
    search_results = qdrant_manager.search_similar(
        collection_name="image_embeddings",
        query_vector=text_embedding,
        limit=limit,
        score_threshold=None,  # Explicitly set to None to return all results
        filter_params=filter_params,
    )
    
    search_time = time.time() - search_start_time
    logger.info(f"Qdrant search took {search_time:.2f} seconds")
    
    logger.info(f"Qdrant search returned {len(search_results)} results")
    
    if not search_results:
        logger.info("No search results found in Qdrant")
        # Return empty results if nothing found
        return SearchResponse(results=[], count=0)
    
    # Log some information about the search results
    for i, result in enumerate(search_results):
        logger.info(f"Result {i+1}: score={result.get('score', 'N/A')}, media_id={result.get('payload', {}).get('media_id', 'N/A')}")
    
    # Get the detailed media information for each result
    results = []
    for result in search_results:
        try:
            # Extract media_id from the payload
            media_id = result.get("payload", {}).get("media_id")
            if not media_id:
                logger.warning(f"Missing media_id in search result: {result}")
                continue
                
            logger.info(f"Processing result with media_id: {media_id}")
                
            # Get the media from database
            media = crud.get_media(db=db, media_id=uuid.UUID(media_id))
            if not media:
                logger.warning(f"Media not found for id: {media_id}")
                continue
                
            # Get the presigned URL for the media
            presigned_url = storage_manager.generate_presigned_url(media.url)
            
            # Create the media response
            media_response = MediaResponse.model_validate(media)
            media_response.presigned_url = presigned_url
            
            # Add to results
            results.append(
                SearchResult(
                    media=media_response,
                    score=result.get("score", 0.0),
                )
            )
            logger.info(f"Added media {media_id} to results with score {result.get('score', 0.0)}")
        except Exception as e:
            logger.error(f"Error processing search result: {str(e)}")
            continue
    
    total_time = time.time() - start_time
    logger.info(f"Total search processing took {total_time:.2f} seconds")
    logger.info(f"Returning {len(results)} search results")
    
    response = SearchResponse(
        results=results,
        count=len(results)
    )
    
    return response 