import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.models.base_models import KeyframeFace

if TYPE_CHECKING:
    from app.models.face import Face
    from app.models.media import Media


class KeyframeBase(SQLModel):
    frame_idx: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class KeyframeCreate(KeyframeBase):
    media_id: uuid.UUID


class KeyframeUpdate(SQLModel):
    frame_idx: int | None = Field(default=None)


class Keyframe(KeyframeBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    media_id: uuid.UUID = Field(foreign_key="media.id")

    # Relationships
    media: "Media" = Relationship(back_populates="keyframes")
    faces: list["Face"] = Relationship(
        back_populates="keyframes", link_model=KeyframeFace
    )


class KeyframeResponse(KeyframeBase):
    id: uuid.UUID
    media_id: uuid.UUID
