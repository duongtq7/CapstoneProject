import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class SearchHistoryBase(SQLModel):
    query: str
    executed_at: datetime = Field(default_factory=datetime.utcnow)


class SearchHistoryCreate(SearchHistoryBase):
    user_id: uuid.UUID


class SearchHistory(SearchHistoryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")

    # Relationships
    user: "User" = Relationship(back_populates="search_history")


class SearchHistoryResponse(SearchHistoryBase):
    id: uuid.UUID
    user_id: uuid.UUID
