import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.media import Media


class MediaEmbeddingBase(SQLModel):
    embedding_id: uuid.UUID  # Qdrant embedding reference
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MediaEmbeddingCreate(MediaEmbeddingBase):
    media_id: uuid.UUID


class MediaEmbeddingUpdate(SQLModel):
    embedding_id: uuid.UUID | None = Field(default=None)


class MediaEmbedding(MediaEmbeddingBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    media_id: uuid.UUID = Field(foreign_key="media.id")

    # Relationships
    media: "Media" = Relationship(back_populates="embeddings")


class MediaEmbeddingResponse(MediaEmbeddingBase):
    id: uuid.UUID
    media_id: uuid.UUID
