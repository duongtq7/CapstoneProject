import uuid
import logging
import time
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlmodel import Session

from app import crud
from app.crud.media import get_media_count_by_user
from app.api.deps import get_current_user, get_db
from app.core.vector_db import qdrant_manager
from app.core.object_storage import storage_manager
from app.core.clip_text_client import clip_text_client
from app.core.translation_client import translation_client
from app.models.media import MediaResponse
from app.models.user import User

router = APIRouter()

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """Model for search results with score and media data."""
    media: MediaResponse
    score: float
    metadata: dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Model for the search endpoint response."""
    results: List[SearchResult]
    count: int
    debug_info: dict[str, Any] = {}


@router.get("/", response_model=SearchResponse)
async def search_media(
    *,
    db: Session = Depends(get_db),
    query: str = Query(..., min_length=1, description="Search query text"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results to return"),
    score_threshold: float = Query(0.1, ge=0.0, le=1.0, description="Minimum similarity score threshold"),
    debug: bool = Query(False, description="Include debug information in the response"),
    translate: bool = Query(True, description="Whether to translate the query from Vietnamese to English"),
    current_user: User = Depends(get_current_user),
) -> SearchResponse:
    """
    Search for media using semantic text search.
    Uses CLIP to convert text to embeddings and finds similar media in Qdrant.
    Optionally translates Vietnamese queries to English before searching.
    """
    # Add more visible console logging
    print("=" * 50)
    print(f"SEARCH ENDPOINT CALLED - Original Query: '{query}'")
    print(f"User ID: {current_user.id}, Email: {current_user.email}")
    print(f"Parameters: limit={limit}, score_threshold={score_threshold}, debug={debug}, translate={translate}")
    print("=" * 50)
    
    logger.info(f"Starting search with query: '{query}' for user: {current_user.id}")
    logger.info(f"Search parameters: limit={limit}, score_threshold={score_threshold}, debug={debug}, translate={translate}")
    
    start_time = time.time()
    debug_info = {
        "original_query": query
    }
    
    try:
        # Translate the query if requested
        original_query = query
        if translate:
            try:
                logger.info(f"Translating query from Vietnamese to English: '{query}'")
                translated_query = await translation_client.translate_vi_to_en(query)
                
                if translated_query != query:
                    logger.info(f"Query translated to: '{translated_query}'")
                    query = translated_query
                    debug_info["translated_query"] = translated_query
                else:
                    logger.info("Query remained the same after translation or translation failed")
                    debug_info["translation_note"] = "No change after translation"
            except Exception as e:
                logger.error(f"Error during translation: {str(e)}")
                debug_info["translation_error"] = str(e)
                # Continue with original query
        
        # Check if user has any media with embeddings
        try:
            user_media_count = get_media_count_by_user(db=db, user_id=current_user.id)
            logger.info(f"User has {user_media_count} media items")
            
            if user_media_count == 0:
                logger.info("User has no media items")
                return SearchResponse(
                    results=[],
                    count=0,
                    debug_info={"message": "No media items found for user", **debug_info} if debug else {}
                )
        except Exception as e:
            logger.error(f"Error getting media count: {str(e)}")
            # Continue with search even if count fails
        
        # Get the text embedding from CLIP API
        logger.info(f"Calling CLIP text encoder API with query: '{query}'")
        try:
            text_embedding = await clip_text_client.get_text_embedding(query)
        except Exception as e:
            error_msg = f"Error calling CLIP text encoder API: {str(e)}"
            logger.error(error_msg)
            # Return empty results with error info instead of raising an exception
            return SearchResponse(
                results=[],
                count=0,
                debug_info={"error": error_msg, "stage": "text_embedding", **debug_info} if debug else {}
            )
        
        embedding_time = time.time() - start_time
        logger.info(f"Text embedding generation took {embedding_time:.2f} seconds")
        
        if debug:
            debug_info["embedding_time"] = embedding_time
        
        if not text_embedding:
            error_msg = "Failed to generate text embedding"
            logger.error(error_msg)
            return SearchResponse(
                results=[],
                count=0,
                debug_info={"error": error_msg, "stage": "text_embedding", **debug_info} if debug else {}
            )
        
        logger.info(f"Successfully generated text embedding with {len(text_embedding)} dimensions")
        
        # Create filter to only search user's media
        filter_params = {
            "user_id": str(current_user.id)
        }
        
        logger.info(f"Searching Qdrant with filter: {filter_params}")
        
        search_start_time = time.time()
        
        # Search Qdrant using the text embedding
        logger.info("Calling Qdrant search...")
        try:
            search_results = qdrant_manager.search_similar(
                collection_name="image_embeddings",
                query_vector=text_embedding,
                limit=limit,
                score_threshold=score_threshold,
                filter_params=filter_params,
            )
        except Exception as e:
            error_msg = f"Error searching Qdrant: {str(e)}"
            logger.error(error_msg)
            # Return empty results with error info instead of raising an exception
            return SearchResponse(
                results=[],
                count=0,
                debug_info={"error": error_msg, "stage": "vector_search", **debug_info} if debug else {}
            )
        
        search_time = time.time() - search_start_time
        logger.info(f"Qdrant search took {search_time:.2f} seconds")
        
        if debug:
            debug_info["search_time"] = search_time
        
        logger.info(f"Qdrant search returned {len(search_results)} results")
        
        if not search_results:
            logger.info("No search results found in Qdrant")
            # Return empty results if nothing found
            return SearchResponse(
                results=[],
                count=0,
                debug_info=debug_info if debug else {}
            )
        
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
                try:
                    media = crud.get_media(db=db, media_id=uuid.UUID(media_id))
                except Exception as e:
                    logger.error(f"Error getting media from database: {str(e)}")
                    continue
                    
                if not media:
                    logger.warning(f"Media not found for id: {media_id}")
                    continue
                    
                # Get the presigned URL for the media
                try:
                    presigned_url = storage_manager.generate_presigned_url(media.url)
                except Exception as e:
                    logger.error(f"Error generating presigned URL: {str(e)}")
                    continue
                
                # Create the media response
                media_response = MediaResponse.model_validate(media)
                media_response.presigned_url = presigned_url
                
                # Add to results
                results.append(
                    SearchResult(
                        media=media_response,
                        score=result.get("score", 0.0),
                        metadata=result.get("payload", {})
                    )
                )
                logger.info(f"Added media {media_id} to results with score {result.get('score', 0.0)}")
            except Exception as e:
                logger.error(f"Error processing search result: {str(e)}")
                continue
        
        total_time = time.time() - start_time
        logger.info(f"Total search processing took {total_time:.2f} seconds")
        logger.info(f"Returning {len(results)} search results")
        
        if debug:
            debug_info.update({
                "total_time": total_time,
                "embedding_dimensions": len(text_embedding),
                "score_threshold": score_threshold,
                "filter_params": filter_params,
                "raw_results_count": len(search_results),
                "processed_results_count": len(results),
                "user_media_count": user_media_count if 'user_media_count' in locals() else None
            })
        
        response = SearchResponse(
            results=results,
            count=len(results),
            debug_info=debug_info if debug else {}
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error during search: {str(e)}")
        # Log the full error details
        import traceback
        logger.error(f"Full error traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during search: {str(e)}"
        ) 