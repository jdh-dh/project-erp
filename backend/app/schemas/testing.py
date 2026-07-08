from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TestType = Literal["UNIT", "INTEGRATION", "FIELD"]
TestResult = Literal["PASS", "FAIL", "BLOCKED"]


class TestCaseCreate(BaseModel):
    test_type: TestType
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    expected_result: str | None = None


class TestCaseUpdate(BaseModel):
    test_type: TestType | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    expected_result: str | None = None


class TestRunCreate(BaseModel):
    run_date: date
    result: TestResult
    note: str | None = None


class TestRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_date: date
    result: TestResult
    tester_id: int
    tester_name: str
    note: str | None


class TestCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_type: TestType
    name: str
    description: str | None
    expected_result: str | None
    last_result: TestResult | None


class TestCaseDetailOut(TestCaseOut):
    runs: list[TestRunOut]
