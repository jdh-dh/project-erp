from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ReportProject(BaseModel):
    code: str
    name: str
    project_type: str
    status: str
    customer_name: str
    manager_name: str
    start_date: date | None
    end_date: date | None


class ReportSchedule(BaseModel):
    progress: float
    wbs_total: int
    wbs_delayed: int
    milestone_total: int
    milestone_delayed: int


class ReportIssues(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int
    closed: int


class ReportTests(BaseModel):
    total: int
    passed: int
    failed: int
    blocked: int
    not_run: int


class ReportHardware(BaseModel):
    boards: int


class ReportSoftware(BaseModel):
    modules: int
    versions: int
    released_versions: int


class ReportCosts(BaseModel):
    total: Decimal
    by_category: dict[str, Decimal]


class ProjectReport(BaseModel):
    project: ReportProject
    schedule: ReportSchedule
    issues: ReportIssues
    tests: ReportTests
    hardware: ReportHardware
    software: ReportSoftware
    releases: int
    costs: ReportCosts
