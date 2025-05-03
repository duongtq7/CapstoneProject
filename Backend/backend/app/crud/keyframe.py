import uuid
from typing import List, Optional

from sqlmodel import Session, select

from app.models.keyframe import Keyframe, KeyframeCreate, KeyframeUpdate


def create_keyframe(db: Session, *, obj_in: KeyframeCreate) -> Keyframe:
    """Create a new keyframe."""
    db_obj = Keyframe(**obj_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_keyframe(db: Session, keyframe_id: uuid.UUID) -> Optional[Keyframe]:
    """Get a keyframe by ID."""
    return db.get(Keyframe, keyframe_id)


def get_keyframes_by_media(
    db: Session, *, media_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[Keyframe]:
    """Get all keyframes for a media item."""
    return list(
        db.exec(
            select(Keyframe)
            .where(Keyframe.media_id == media_id)
            .offset(skip)
            .limit(limit)
        )
    )


def update_keyframe(
    db: Session, *, db_obj: Keyframe, obj_in: KeyframeUpdate
) -> Keyframe:
    """Update a keyframe."""
    update_data = obj_in.model_dump(exclude_unset=True)
    for field in update_data:
        setattr(db_obj, field, update_data[field])
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_keyframe(db: Session, *, db_obj: Keyframe) -> None:
    """Delete a keyframe."""
    db.delete(db_obj)
    db.commit()


def delete_keyframes_by_media(db: Session, *, media_id: uuid.UUID) -> None:
    """Delete all keyframes for a media item."""
    keyframes = get_keyframes_by_media(db=db, media_id=media_id)
    for keyframe in keyframes:
        delete_keyframe(db=db, db_obj=keyframe) 