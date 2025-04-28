import uuid

from sqlmodel import Session, select

from app.models.media_metadata import (
    MediaMetadata,
    MediaMetadataCreate,
    MediaMetadataUpdate,
)


def create_media_metadata(db: Session, *, obj_in: MediaMetadataCreate) -> MediaMetadata:
    """Create metadata for a media item."""
    media_metadata = MediaMetadata(**obj_in.model_dump())
    db.add(media_metadata)
    db.commit()
    db.refresh(media_metadata)
    return media_metadata


def get_media_metadata(db: Session, media_id: uuid.UUID) -> MediaMetadata | None:
    """Get metadata for a media item."""
    return db.exec(
        select(MediaMetadata).where(MediaMetadata.media_id == media_id)
    ).first()


def update_media_metadata(
    db: Session, *, db_obj: MediaMetadata, obj_in: MediaMetadataUpdate
) -> MediaMetadata:
    """Update metadata for a media item."""
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_media_metadata(db: Session, *, db_obj: MediaMetadata) -> None:
    """Delete metadata for a media item."""
    db.delete(db_obj)
    db.commit()
