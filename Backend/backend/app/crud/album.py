import uuid

from sqlmodel import Session, select

from app.models.album import Album, AlbumCreate, AlbumUpdate


def create_album(db: Session, *, obj_in: AlbumCreate, user_id: uuid.UUID) -> Album:
    """Create a new album for a user."""
    album = Album(**obj_in.model_dump(), user_id=user_id)
    db.add(album)
    db.commit()
    db.refresh(album)
    return album


def get_album(db: Session, album_id: uuid.UUID) -> Album | None:
    """Get an album by its ID."""
    return db.exec(select(Album).where(Album.id == album_id)).first()


def get_albums_by_user(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[Album]:
    """Get all albums for a user."""
    return db.exec(
        select(Album).where(Album.user_id == user_id).offset(skip).limit(limit)
    ).all()


def update_album(db: Session, *, db_obj: Album, obj_in: AlbumUpdate) -> Album:
    """Update an album."""
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_album(db: Session, *, db_obj: Album) -> None:
    """Delete an album."""
    db.delete(db_obj)
    db.commit()
