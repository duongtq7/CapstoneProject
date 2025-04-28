import uuid

from sqlmodel import Session, select

from app.models.media import Media, MediaCreate, MediaUpdate


def create_media(db: Session, *, obj_in: MediaCreate) -> Media:
    """Create a new media item."""
    media = Media(**obj_in.model_dump())
    db.add(media)
    db.commit()
    db.refresh(media)
    return media


def get_media(db: Session, media_id: uuid.UUID) -> Media | None:
    """Get a media item by its ID."""
    return db.exec(select(Media).where(Media.id == media_id)).first()


def get_media_by_album(
    db: Session, album_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[Media]:
    """Get all media items for an album."""
    return db.exec(
        select(Media).where(Media.album_id == album_id).offset(skip).limit(limit)
    ).all()


def update_media(db: Session, *, db_obj: Media, obj_in: MediaUpdate) -> Media:
    """Update a media item."""
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_media(db: Session, *, db_obj: Media) -> None:
    """Delete a media item."""
    db.delete(db_obj)
    db.commit()
