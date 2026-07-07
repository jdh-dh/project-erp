from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProjectType = Literal["HW", "SW", "HYBRID"]
ProjectStatus = Literal["PLANNED", "IN_PROGRESS", "ON_HOLD", "COMPLETED", "CANCELED"]
ContractStatus = Literal["ACTIVE", "CLOSED", "CANCELED"]


class ProjectCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=200)
    customer_id: int
    project_type: ProjectType
    manager_id: int
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    customer_id: int | None = None
    project_type: ProjectType | None = None
    manager_id: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None


class ProjectStatusUpdate(BaseModel):
    status: ProjectStatus


class MemberIn(BaseModel):
    user_id: int
    role: str | None = Field(default=None, max_length=50)


class MembersSet(BaseModel):
    members: list[MemberIn]


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    role: str | None
    user_name: str


class ContractCreate(BaseModel):
    contract_no: str = Field(min_length=1, max_length=100)
    amount: Decimal | None = None
    signed_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    note: str | None = None


class ContractUpdate(BaseModel):
    contract_no: str | None = Field(default=None, min_length=1, max_length=100)
    amount: Decimal | None = None
    signed_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: ContractStatus | None = None
    note: str | None = None


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_no: str
    amount: Decimal | None
    signed_date: date | None
    start_date: date | None
    end_date: date | None
    status: ContractStatus
    note: str | None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    customer_id: int
    customer_name: str
    project_type: ProjectType
    status: ProjectStatus
    manager_id: int
    manager_name: str
    start_date: date | None
    end_date: date | None
    created_at: datetime


class ProjectDetailOut(ProjectOut):
    description: str | None
    members: list[MemberOut]
    contracts: list[ContractOut]
