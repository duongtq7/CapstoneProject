import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.media import Media
    from app.models.user import User


class AlbumBase(SQLModel):
    title: str = Field(max_length=255)
    description: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AlbumCreate(AlbumBase):
    pass


class AlbumUpdate(SQLModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Album(AlbumBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)

    # Relationships
    user: "User" = Relationship(back_populates="albums")
    media_items: list["Media"] = Relationship(back_populates="album")


class AlbumResponse(AlbumBase):
    id: uuid.UUID
    user_id: uuid.UUID
