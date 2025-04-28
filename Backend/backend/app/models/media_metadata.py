import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.media import Media


class MediaMetadataBase(SQLModel):
    width: int | None = Field(default=None)
    height: int | None = Field(default=None)
    duration: float | None = Field(default=None)  # Duration in seconds for videos
    fps: float | None = Field(default=None)  # Frames per second for videos
    mime_type: str | None = Field(default=None, max_length=50)
    resolution: str | None = Field(default=None, max_length=20)
    gps_latitude: float | None = Field(default=None)
    gps_longitude: float | None = Field(default=None)
    capture_date: datetime | None = Field(default=None)


class MediaMetadataCreate(MediaMetadataBase):
    media_id: uuid.UUID


class MediaMetadataUpdate(SQLModel):
    width: int | None = Field(default=None)
    height: int | None = Field(default=None)
    duration: float | None = Field(default=None)
    fps: float | None = Field(default=None)
    mime_type: str | None = Field(default=None, max_length=50)
    resolution: str | None = Field(default=None, max_length=20)
    gps_latitude: float | None = Field(default=None)
    gps_longitude: float | None = Field(default=None)
    capture_date: datetime | None = Field(default=None)


class MediaMetadata(MediaMetadataBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    media_id: uuid.UUID = Field(foreign_key="media.id", unique=True)

    # Relationships
    media: "Media" = Relationship(back_populates="media_metadata")


class MediaMetadataResponse(MediaMetadataBase):
    id: uuid.UUID
    media_id: uuid.UUID
