import uuid
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session

from app import crud
from app.api.deps import get_current_user, get_db
from app.core.object_storage import storage_manager
from app.core.vector_db import qdrant_manager
from app.core.clip_client import clip_client
from app.models.media import MediaCreate, MediaResponse
from app.models.media_embedding import MediaEmbeddingCreate
from app.models.user import User

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post(
    "/upload", response_model=MediaResponse, status_code=status.HTTP_201_CREATED
)
async def upload_media(
    *,
    db: Session = Depends(get_db),
    file: UploadFile = File(...),
    album_id: uuid.UUID = Form(...),
    current_user: User = Depends(get_current_user),
) -> MediaResponse:
    """
    Upload a new media file to a specific album.
    """
    # Check if album exists and belongs to the current user
    album = crud.get_album(db=db, album_id=album_id)
    if not album:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Album not found",
        )
    if album.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Determine media type from file content type
    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        media_type = "photo"
    elif content_type.startswith("video/"):
        media_type = "video"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )

    # Upload file to object storage
    success, url, object_key = await storage_manager.upload_file(
        user_id=current_user.id,
        album_id=album_id,
        file=file,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file",
        )

    # Create media entry in database
    media_in = MediaCreate(
        media_type=media_type,
        url=object_key,
        file_size=file.size,
        album_id=album_id,
    )
    media = crud.create_media(db=db, obj_in=media_in)

    # Generate embedding for images using CLIP API
    if media_type == "photo":
        try:
            # Generate a presigned URL for the CLIP API to access
            presigned_url = storage_manager.generate_presigned_url(object_key)
            
            # Call CLIP API to get embedding with both URL and object key
            embedding_vector = await clip_client.get_image_embedding(presigned_url, object_key)
            
            if embedding_vector:
                # Generate a unique ID for the embedding in Qdrant
                embedding_id = str(uuid.uuid4())
                
                # Store the embedding in Qdrant
                qdrant_success = qdrant_manager.create_point(
                    collection_name="image_embeddings",
                    vector=embedding_vector,
                    point_id=embedding_id,
                    payload={
                        "media_id": str(media.id),
                        "user_id": str(current_user.id),
                        "album_id": str(album_id),
                    },
                )
                
                if qdrant_success:
                    # Create a record in the database linking the media to its embedding
                    embedding_in = MediaEmbeddingCreate(
                        media_id=media.id,
                        embedding_id=uuid.UUID(embedding_id),
                    )
                    crud.create_media_embedding(db=db, obj_in=embedding_in)
            else:
                # Log error but continue with upload - don't fail the whole operation
                logger.error(f"Failed to generate embedding for media {media.id}")
        except Exception as e:
            # Log error but continue with upload - don't fail the whole operation
            logger.error(f"Error during embedding generation: {str(e)}")

    # TODO: Extract metadata from file and create MediaMetadata

    # Create MediaResponse from Media model and add presigned URL
    media_response = MediaResponse.model_validate(media)
    media_response.presigned_url = storage_manager.generate_presigned_url(media.url)

    return media_response


@router.get("/", response_model=list[MediaResponse])
async def read_media_items(
    *,
    db: Session = Depends(get_db),
    album_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
) -> list[MediaResponse]:
    """
    Retrieve all media items, optionally filtered by album.
    """
    if album_id:
        # Check if album belongs to the current user
        album = crud.get_album(db=db, album_id=album_id)
        if not album:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Album not found",
            )
        if album.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        media_items = crud.get_media_by_album(
            db=db, album_id=album_id, skip=skip, limit=limit
        )
    else:
        # Get all media from all user's albums
        media_items = []
        albums = crud.get_albums_by_user(db=db, user_id=current_user.id)
        for album in albums:
            album_media = crud.get_media_by_album(
                db=db, album_id=album.id, skip=skip, limit=limit
            )
            media_items.extend(album_media)

    # Convert Media models to MediaResponse models with presigned URLs
    response_items = []
    for media in media_items:
        # Create MediaResponse from Media model
        media_response = MediaResponse.model_validate(media)
        # Add presigned URL
        media_response.presigned_url = storage_manager.generate_presigned_url(media.url)
        response_items.append(media_response)

    return response_items


@router.get("/{media_id}", response_model=MediaResponse)
async def read_media(
    *,
    db: Session = Depends(get_db),
    media_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
) -> MediaResponse:
    """
    Get a specific media item by ID.
    """
    media = crud.get_media(db=db, media_id=media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found",
        )

    # Check if media belongs to one of user's albums
    album = crud.get_album(db=db, album_id=media.album_id)
    if not album or album.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Create MediaResponse from Media model and add presigned URL
    media_response = MediaResponse.model_validate(media)
    media_response.presigned_url = storage_manager.generate_presigned_url(media.url)

    return media_response


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media(
    *,
    db: Session = Depends(get_db),
    media_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a media item.
    """
    media = crud.get_media(db=db, media_id=media_id)
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media not found",
        )

    # Check if media belongs to one of user's albums
    album = crud.get_album(db=db, album_id=media.album_id)
    if not album or album.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    # Delete file from object storage
    if media.url:
        storage_manager.delete_file(media.url)

    # Delete any embeddings from Qdrant
    embeddings = crud.get_media_embeddings_by_media(db=db, media_id=media_id)
    for embedding in embeddings:
        # Delete from Qdrant
        qdrant_manager.delete_point(
            collection_name="image_embeddings" if media.media_type == "photo" else "video_embeddings",
            point_id=str(embedding.embedding_id),
        )
        # Delete from database
        crud.delete_media_embedding(db=db, db_obj=embedding)

    # Delete the media item itself
    crud.delete_media(db=db, db_obj=media)
