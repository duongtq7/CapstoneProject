import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.base_models import KeyframeFace, MediaFace

if TYPE_CHECKING:
    from app.models.face_embedding import FaceEmbedding
    from app.models.keyframe import Keyframe
    from app.models.media import Media


class FaceBase(SQLModel):
    name: str | None = Field(default=None, max_length=100)
    avatar: str | None = Field(default=None)  # URL or path to avatar image
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FaceCreate(FaceBase):
    pass


class FaceUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100)
    avatar: str | None = Field(default=None)


class Face(FaceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Relationships
    media_items: list["Media"] = Relationship(
        back_populates="faces", link_model=MediaFace
    )
    keyframes: list["Keyframe"] = Relationship(
        back_populates="faces", link_model=KeyframeFace
    )
    embeddings: list["FaceEmbedding"] = Relationship(back_populates="face")


class FaceResponse(FaceBase):
    id: uuid.UUID
