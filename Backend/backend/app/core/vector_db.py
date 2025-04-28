from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    CollectionStatus,
    Distance,
    PointStruct,
    VectorParams,
)

from app.core.config import settings


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
        existing_collections = self.client.get_collections().collections
        existing_collection_names = [c.name for c in existing_collections]

        for collection_name, params in self._collections.items():
            if collection_name not in existing_collection_names:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=params["vector_size"],
                        distance=params["distance"],
                    ),
                )

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
            self.client.upsert(
                collection_name=collection_name,
                points=[PointStruct(id=point_id, vector=vector, payload=payload or {})],
            )
            return True
        except Exception as e:
            print(f"Error creating point: {e}")
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
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_params,
            )
            return [
                {
                    "id": str(result.id),
                    "score": result.score,
                    "payload": result.payload,
                }
                for result in results
            ]
        except Exception as e:
            print(f"Error searching for similar vectors: {e}")
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
