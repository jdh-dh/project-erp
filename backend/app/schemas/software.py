from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ModuleType = Literal["FIRMWARE", "APP", "SERVER", "LIBRARY"]
VersionStatus = Literal["DEVELOP", "RELEASED", "DEPRECATED"]
BuildResult = Literal["SUCCESS", "FAIL"]
DeployEnvironment = Literal["DEV", "STAGE", "PROD", "FIELD"]


class ModuleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    module_type: ModuleType
    repo_url: str | None = Field(default=None, max_length=300)
    description: str | None = None


class ModuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    module_type: ModuleType | None = None
    repo_url: str | None = Field(default=None, max_length=300)
    description: str | None = None


class VersionCreate(BaseModel):
    version: str = Field(min_length=1, max_length=50)
    note: str | None = None


class VersionUpdate(BaseModel):
    version: str | None = Field(default=None, min_length=1, max_length=50)
    status: VersionStatus | None = None
    note: str | None = None


class BuildCreate(BaseModel):
    build_no: str = Field(min_length=1, max_length=50)
    commit_hash: str | None = Field(default=None, max_length=64)
    result: BuildResult = "SUCCESS"
    note: str | None = None


class BuildOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    build_no: str
    commit_hash: str | None
    built_at: datetime
    result: BuildResult
    note: str | None


class DeploymentCreate(BaseModel):
    environment: DeployEnvironment
    note: str | None = None


class DeploymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    environment: DeployEnvironment
    deployed_at: datetime
    note: str | None


class VersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version: str
    status: VersionStatus
    released_date: date | None
    note: str | None


class VersionDetailOut(VersionOut):
    builds: list[BuildOut]
    deployments: list[DeploymentOut]


class ModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    module_type: ModuleType
    repo_url: str | None
    description: str | None


class ModuleDetailOut(ModuleOut):
    versions: list[VersionOut]
