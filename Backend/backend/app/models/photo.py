import uuid

from pydantic import HttpUrl
from sqlalchemy.types import String, TypeDecorator
from sqlmodel import Field, Relationship, SQLModel

from app.models.user import User


class HttpUrlType(TypeDecorator):
    impl = String(2083)
    cache_ok = True
    python_type = HttpUrl

    def process_bind_param(self, value, dialect) -> str:
        return str(value)

    def process_result_value(self, value, dialect) -> HttpUrl:
        return HttpUrl(url=value)

    def process_literal_param(self, value, dialect) -> str:
        return str(value)


class PhotoBase(SQLModel):
    # title: str = Field(min_length=1, max_length=255)
    # description: str | None = Field(default=None, max_length=255)
    url: HttpUrl = Field(
        index=True,
        unique=True,
        nullable=False,
        sa_type=HttpUrlType,
    )
    description: str | None = Field(default=None, max_length=255)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)


# Properties to receive on item creation
class PhotoCreate(PhotoBase):
    pass


# Database model, database table inferred from class name
class Photo(PhotoBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="photos")
