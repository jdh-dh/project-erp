from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CostCategory = Literal["LABOR", "MATERIAL", "OUTSOURCING", "EQUIPMENT", "ETC"]


class CostCreate(BaseModel):
    cost_date: date
    category: CostCategory
    item: str = Field(min_length=1, max_length=300)
    amount: Decimal = Field(gt=0)
    note: str | None = None


class CostUpdate(BaseModel):
    cost_date: date | None = None
    category: CostCategory | None = None
    item: str | None = Field(default=None, min_length=1, max_length=300)
    amount: Decimal | None = Field(default=None, gt=0)
    note: str | None = None


class CostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cost_date: date
    category: CostCategory
    item: str
    amount: Decimal
    note: str | None
    created_by: int
    creator_name: str


class CostSummary(BaseModel):
    total: Decimal
    by_category: dict[str, Decimal]
