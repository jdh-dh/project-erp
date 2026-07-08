from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BoardStatus = Literal["DESIGN", "PROTOTYPE", "PRODUCTION", "OBSOLETE"]
FabResult = Literal["OK", "NG", "PARTIAL"]


class BoardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    revision: str = Field(min_length=1, max_length=50)
    status: BoardStatus = "DESIGN"
    description: str | None = None


class BoardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    revision: str | None = Field(default=None, min_length=1, max_length=50)
    status: BoardStatus | None = None
    description: str | None = None


class BomItemCreate(BaseModel):
    part_name: str = Field(min_length=1, max_length=200)
    part_number: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=100)
    quantity: int = Field(default=1, ge=1)
    reference: str | None = Field(default=None, max_length=100)
    note: str | None = None


class BomItemUpdate(BaseModel):
    part_name: str | None = Field(default=None, min_length=1, max_length=200)
    part_number: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=100)
    quantity: int | None = Field(default=None, ge=1)
    reference: str | None = Field(default=None, max_length=100)
    note: str | None = None


class BomItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    part_name: str
    part_number: str | None
    manufacturer: str | None
    quantity: int
    reference: str | None
    note: str | None


class FabricationCreate(BaseModel):
    fab_date: date
    quantity: int = Field(ge=1)
    vendor: str | None = Field(default=None, max_length=200)
    result: FabResult = "OK"
    note: str | None = None


class FabricationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fab_date: date
    quantity: int
    vendor: str | None
    result: FabResult
    note: str | None


class BoardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    revision: str
    status: BoardStatus
    description: str | None


class BoardDetailOut(BoardOut):
    bom_items: list[BomItemOut]
    fabrications: list[FabricationOut]
