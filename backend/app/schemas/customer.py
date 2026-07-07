from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    position: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)


class ContactUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    position: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    position: str | None
    phone: str | None
    email: str | None
    is_active: bool


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    business_no: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=300)
    note: str | None = None


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    business_no: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=300)
    note: str | None = None


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    business_no: str | None
    address: str | None
    note: str | None
    is_active: bool
    created_at: datetime


class CustomerDetailOut(CustomerOut):
    contacts: list[ContactOut]
