from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

WbsStatus = Literal["TODO", "IN_PROGRESS", "DONE"]
MilestoneStatus = Literal["PENDING", "ACHIEVED"]


class WbsCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    parent_id: int | None = None
    assignee_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    progress: int = Field(default=0, ge=0, le=100)
    status: WbsStatus = "TODO"
    sort_order: int = 0


class WbsUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None
    assignee_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    progress: int | None = Field(default=None, ge=0, le=100)
    status: WbsStatus | None = None
    sort_order: int | None = None


class WbsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: int | None
    name: str
    assignee_id: int | None
    assignee_name: str | None
    start_date: date | None
    end_date: date | None
    progress: int
    status: WbsStatus
    sort_order: int
    depth: int
    is_delayed: bool


class MilestoneCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    due_date: date
    note: str | None = None


class MilestoneUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    due_date: date | None = None
    note: str | None = None


class MilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    due_date: date
    status: MilestoneStatus
    achieved_date: date | None
    note: str | None
    is_delayed: bool


class ScheduleSummary(BaseModel):
    progress: float
    wbs_total: int
    wbs_delayed: int
    milestone_total: int
    milestone_delayed: int
