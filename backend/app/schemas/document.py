from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DocType = Literal[
    "REQUIREMENTS",
    "DESIGN",
    "INTERFACE",
    "TEST_PLAN",
    "VERIFICATION",
    "RELEASE_NOTE",
    "OTHER",
]


class DocumentCreate(BaseModel):
    doc_type: DocType
    title: str = Field(min_length=1, max_length=300)
    version: str = Field(default="1.0", min_length=1, max_length=50)
    file_url: str | None = Field(default=None, max_length=500)
    description: str | None = None


class DocumentUpdate(BaseModel):
    doc_type: DocType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    version: str | None = Field(default=None, min_length=1, max_length=50)
    file_url: str | None = Field(default=None, max_length=500)
    description: str | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doc_type: DocType
    title: str
    version: str
    file_url: str | None
    description: str | None
    author_id: int
    author_name: str
    updated_at: datetime
