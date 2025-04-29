from app.crud.album import (
    create_album,
    delete_album,
    get_album,
    get_albums_by_user,
    update_album,
)
from app.crud.media import (
    create_media,
    delete_media,
    get_media,
    get_media_by_album,
    update_media,
    get_media_count_by_user,
)
from app.crud.media_embedding import (
    create_media_embedding,
    delete_media_embedding,
    get_media_embedding,
    get_media_embeddings_by_media,
    update_media_embedding,
)
from app.crud.media_metadata import (
    create_media_metadata,
    delete_media_metadata,
    get_media_metadata,
    update_media_metadata,
)
from app.crud.user import (
    authenticate,
    create_user,
    get_user_by_email,
    update_user,
)

__all__ = [
    # Album operations
    "create_album",
    "delete_album",
    "get_album",
    "get_albums_by_user",
    "update_album",
    # Media operations
    "create_media",
    "delete_media",
    "get_media",
    "get_media_by_album",
    "update_media",
    "get_media_count_by_user",
    # Media embedding operations
    "create_media_embedding",
    "delete_media_embedding",
    "get_media_embedding",
    "get_media_embeddings_by_media",
    "update_media_embedding",
    # Media metadata operations
    "create_media_metadata",
    "delete_media_metadata",
    "get_media_metadata",
    "update_media_metadata",
    # User operations
    "authenticate",
    "create_user",
    "get_user_by_email",
    "update_user",
]
