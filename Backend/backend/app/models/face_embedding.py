import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.face import Face


class FaceEmbeddingBase(SQLModel):
    embedding_id: uuid.UUID  # Qdrant embedding reference
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FaceEmbeddingCreate(FaceEmbeddingBase):
    face_id: uuid.UUID


class FaceEmbeddingUpdate(SQLModel):
    embedding_id: uuid.UUID | None = Field(default=None)


class FaceEmbedding(FaceEmbeddingBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    face_id: uuid.UUID = Field(foreign_key="face.id")

    # Relationships
    face: "Face" = Relationship(back_populates="embeddings")


class FaceEmbeddingResponse(FaceEmbeddingBase):
    id: uuid.UUID
    face_id: uuid.UUID
