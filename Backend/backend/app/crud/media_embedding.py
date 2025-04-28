import uuid

from sqlmodel import Session, select

from app.models.media_embedding import MediaEmbedding, MediaEmbeddingCreate, MediaEmbeddingUpdate


def create_media_embedding(db: Session, *, obj_in: MediaEmbeddingCreate) -> MediaEmbedding:
    """Create a new media embedding."""
    media_embedding = MediaEmbedding(**obj_in.model_dump())
    db.add(media_embedding)
    db.commit()
    db.refresh(media_embedding)
    return media_embedding


def get_media_embedding(db: Session, embedding_id: uuid.UUID) -> MediaEmbedding | None:
    """Get a media embedding by its ID."""
    return db.exec(select(MediaEmbedding).where(MediaEmbedding.id == embedding_id)).first()


def get_media_embeddings_by_media(
    db: Session, media_id: uuid.UUID
) -> list[MediaEmbedding]:
    """Get all embeddings for a media item."""
    return db.exec(
        select(MediaEmbedding).where(MediaEmbedding.media_id == media_id)
    ).all()


def update_media_embedding(
    db: Session, *, db_obj: MediaEmbedding, obj_in: MediaEmbeddingUpdate
) -> MediaEmbedding:
    """Update a media embedding."""
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_media_embedding(db: Session, *, db_obj: MediaEmbedding) -> None:
    """Delete a media embedding."""
    db.delete(db_obj)
    db.commit() 