import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.models.base_models import MediaFace

if TYPE_CHECKING:
    from app.models.album import Album
    from app.models.face import Face
    from app.models.keyframe import Keyframe
    from app.models.media_embedding import MediaEmbedding
    from app.models.media_metadata import MediaMetadata


class MediaBase(SQLModel):
    media_type: str = Field(max_length=10)  # "photo", "video", "audio", "document"
    url: str = Field(index=True)
    file_size: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MediaCreate(MediaBase):
    album_id: uuid.UUID | None = Field(default=None)


class MediaUpdate(SQLModel):
    media_type: str | None = Field(default=None, max_length=10)
    url: str | None = Field(default=None)
    file_size: int | None = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    album_id: uuid.UUID | None = Field(default=None)


class Media(MediaBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    album_id: uuid.UUID | None = Field(default=None, foreign_key="album.id")

    # Relationships
    album: Optional["Album"] = Relationship(back_populates="media_items")
    media_metadata: Optional["MediaMetadata"] = Relationship(
        back_populates="media", sa_relationship_kwargs={"uselist": False}
    )
    faces: list["Face"] = Relationship(
        back_populates="media_items", link_model=MediaFace
    )
    embeddings: list["MediaEmbedding"] = Relationship(back_populates="media")
    keyframes: list["Keyframe"] = Relationship(back_populates="media")


class MediaResponse(MediaBase):
    id: uuid.UUID
    album_id: uuid.UUID | None
    presigned_url: str | None = None
