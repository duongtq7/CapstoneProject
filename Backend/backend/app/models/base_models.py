import uuid

from sqlmodel import Field, SQLModel


# Junction table for Media and Face
class MediaFace(SQLModel, table=True):
    media_id: uuid.UUID = Field(foreign_key="media.id", primary_key=True)
    face_id: uuid.UUID = Field(foreign_key="face.id", primary_key=True)


# Junction table for Keyframe and Face
class KeyframeFace(SQLModel, table=True):
    keyframe_id: uuid.UUID = Field(foreign_key="keyframe.id", primary_key=True)
    face_id: uuid.UUID = Field(foreign_key="face.id", primary_key=True)
