from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ReleaseCreate(BaseModel):
    version: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=300)
    release_date: date
    content: str | None = None


class ReleaseUpdate(BaseModel):
    version: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = Field(default=None, min_length=1, max_length=300)
    release_date: date | None = None
    content: str | None = None


class ReleaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: str
    title: str
    release_date: date
    content: str | None
    created_by: int
    creator_name: str
