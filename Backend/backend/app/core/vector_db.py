from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    CollectionStatus,
    Distance,
    PointStruct,
    VectorParams,
)

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class QdrantManager:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
        )
        self._collections = {
            "image_embeddings": {
                "vector_size": 512,  # CLIP embedding size
                "distance": Distance.COSINE,
            },
            "video_embeddings": {
                "vector_size": 512,  # CLIP embedding size
                "distance": Distance.COSINE,
            },
            "face_embeddings": {
                "vector_size": 512,  # Face embedding size
                "distance": Distance.COSINE,
            },
        }
        self._initialize_collections()

    def _initialize_collections(self) -> None:
        """Initialize all required Qdrant collections if they don't exist."""
        try:
            existing_collections = self.client.get_collections().collections
            existing_collection_names = [c.name for c in existing_collections]
            
            logger.info(f"Existing collections: {existing_collection_names}")

            for collection_name, params in self._collections.items():
                if collection_name not in existing_collection_names:
                    logger.info(f"Creating collection: {collection_name}")
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=params["vector_size"],
                            distance=params["distance"],
                        ),
                    )
                    logger.info(f"Successfully created collection: {collection_name}")
                else:
                    logger.info(f"Collection already exists: {collection_name}")
                    
        except Exception as e:
            logger.error(f"Error initializing collections: {str(e)}")
            logger.error("Collection initialization failed, some operations may fail")

    def check_collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        try:
            collection_info = self.client.get_collection(
                collection_name=collection_name
            )
            return collection_info.status == CollectionStatus.GREEN
        except Exception:
            return False

    def create_point(
        self,
        collection_name: str,
        vector: list[float],
        point_id: str,
        payload: dict[str, Any] | None = None,
    ) -> bool:
        """Create a point in the specified collection."""
        try:
            # Check if collection exists
            if not self.check_collection_exists(collection_name):
                logger.error(f"Collection '{collection_name}' does not exist")
                
                # Try to create the collection if it's in our defined collections
                if collection_name in self._collections:
                    logger.info(f"Attempting to create missing collection: {collection_name}")
                    params = self._collections[collection_name]
                    
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=VectorParams(
                            size=params["vector_size"],
                            distance=params["distance"],
                        ),
                    )
                    logger.info(f"Successfully created collection: {collection_name}")
                else:
                    logger.error(f"Cannot create unknown collection: {collection_name}")
                    return False
            
            # Now create the point
            self.client.upsert(
                collection_name=collection_name,
                points=[PointStruct(id=point_id, vector=vector, payload=payload or {})],
            )
            logger.info(f"Successfully created point {point_id} in collection {collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating point: {e}")
            return False

    def search_similar(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        filter_params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors in the specified collection."""
        # Verify collection exists
        if not self.check_collection_exists(collection_name):
            print(f"Collection '{collection_name}' does not exist")
            return []
        
        # Format the filter parameters correctly for Qdrant
        formatted_filter = None
        if filter_params:
            # Create a properly formatted filter for Qdrant
            # Instead of nested payload structure, create a filter with conditions
            formatted_filter = {
                "must": []
            }
            
            for key, value in filter_params.items():
                if key and value:
                    # Add a match condition for each key-value pair
                    formatted_filter["must"].append({
                        "key": key,
                        "match": {
                            "value": value
                        }
                    })
        
        # Log search parameters
        print(f"Searching collection '{collection_name}' with:")
        print(f"- Query vector dimensions: {len(query_vector)}")
        print(f"- Limit: {limit}")
        print(f"- Score threshold: {score_threshold}")
        print(f"- Raw filter params: {filter_params}")
        print(f"- Formatted filter: {formatted_filter}")
        
        # Try different filter formats if needed
        filter_attempts = [
            formatted_filter,  # First try with our formatted filter
            None,              # Then try with no filter as backup
        ]
        
        for attempt_num, current_filter in enumerate(filter_attempts):
            try:
                print(f"Attempt #{attempt_num+1} with filter: {current_filter}")
                
                # Perform the search
                results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=limit,
                    score_threshold=score_threshold,
                    query_filter=current_filter,
                )
                
                # Log results
                print(f"Found {len(results)} results in attempt #{attempt_num+1}")
                for i, result in enumerate(results):
                    print(f"Result {i+1}:")
                    print(f"- ID: {result.id}")
                    print(f"- Score: {result.score}")
                    print(f"- Payload: {result.payload}")
                
                return [
                    {
                        "id": str(result.id),
                        "score": result.score,
                        "payload": result.payload,
                    }
                    for result in results
                ]
                
            except Exception as e:
                print(f"Error in search attempt #{attempt_num+1}: {e}")
                if attempt_num < len(filter_attempts) - 1:
                    print("Trying next filter format...")
                else:
                    print("All filter formats failed.")
                    import traceback
                    print(f"Full error traceback from last attempt: {traceback.format_exc()}")
                    return []
        
        # Should not reach here, but just in case
        return []

    def delete_point(self, collection_name: str, point_id: str) -> bool:
        """Delete a point from the specified collection."""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=[point_id],
            )
            return True
        except Exception as e:
            print(f"Error deleting point: {e}")
            return False


# Singleton instance
qdrant_manager = QdrantManager()
