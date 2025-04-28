from app.models.album import Album, AlbumCreate, AlbumResponse, AlbumUpdate
from app.models.base_models import KeyframeFace, MediaFace
from app.models.face import Face, FaceCreate, FaceResponse, FaceUpdate
from app.models.face_embedding import (
    FaceEmbedding,
    FaceEmbeddingCreate,
    FaceEmbeddingResponse,
    FaceEmbeddingUpdate,
)
from app.models.keyframe import (
    Keyframe,
    KeyframeCreate,
    KeyframeResponse,
    KeyframeUpdate,
)
from app.models.media import Media, MediaCreate, MediaResponse, MediaUpdate
from app.models.media_embedding import (
    MediaEmbedding,
    MediaEmbeddingCreate,
    MediaEmbeddingResponse,
    MediaEmbeddingUpdate,
)
from app.models.media_metadata import (
    MediaMetadata,
    MediaMetadataCreate,
    MediaMetadataResponse,
    MediaMetadataUpdate,
)
from app.models.search_history import (
    SearchHistory,
    SearchHistoryCreate,
    SearchHistoryResponse,
)
from app.models.user import (
    NewPassword,
    Token,
    TokenPayload,
    UpdatePassword,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)

__all__ = [
    # Album models
    "Album",
    "AlbumCreate",
    "AlbumResponse",
    "AlbumUpdate",
    # Base models
    "MediaFace",
    "KeyframeFace",
    # Face models
    "Face",
    "FaceCreate",
    "FaceResponse",
    "FaceUpdate",
    # Face embedding models
    "FaceEmbedding",
    "FaceEmbeddingCreate",
    "FaceEmbeddingResponse",
    "FaceEmbeddingUpdate",
    # Keyframe models
    "Keyframe",
    "KeyframeCreate",
    "KeyframeResponse",
    "KeyframeUpdate",
    # Media models
    "Media",
    "MediaCreate",
    "MediaResponse",
    "MediaUpdate",
    # Media embedding models
    "MediaEmbedding",
    "MediaEmbeddingCreate",
    "MediaEmbeddingResponse",
    "MediaEmbeddingUpdate",
    # Media metadata models
    "MediaMetadata",
    "MediaMetadataCreate",
    "MediaMetadataResponse",
    "MediaMetadataUpdate",
    # Search history models
    "SearchHistory",
    "SearchHistoryCreate",
    "SearchHistoryResponse",
    # User models
    "NewPassword",
    "Token",
    "TokenPayload",
    "UpdatePassword",
    "User",
    "UserCreate",
    "UserPublic",
    "UserRegister",
    "UserUpdate",
    "UserUpdateMe",
    "UsersPublic",
]
