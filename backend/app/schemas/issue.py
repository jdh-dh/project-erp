from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

IssueType = Literal["BUG", "IMPROVEMENT", "CUSTOMER_REQUEST", "FAILURE"]
IssueSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
IssueStatus = Literal["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]


class IssueCreate(BaseModel):
    issue_type: IssueType
    title: str = Field(min_length=1, max_length=300)
    description: str | None = None
    severity: IssueSeverity = "MEDIUM"
    assignee_id: int | None = None


class IssueUpdate(BaseModel):
    issue_type: IssueType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    severity: IssueSeverity | None = None
    assignee_id: int | None = None
    cause_analysis: str | None = None
    resolution: str | None = None


class IssueStatusUpdate(BaseModel):
    status: IssueStatus
    resolution: str | None = None


class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_type: IssueType
    title: str
    severity: IssueSeverity
    status: IssueStatus
    reporter_id: int
    reporter_name: str
    assignee_id: int | None
    assignee_name: str | None
    resolved_date: date | None
    created_at: datetime


class IssueDetailOut(IssueOut):
    description: str | None
    cause_analysis: str | None
    resolution: str | None
