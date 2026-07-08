from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.schemas.testing import (
    TestCaseCreate,
    TestCaseDetailOut,
    TestCaseOut,
    TestCaseUpdate,
    TestRunCreate,
    TestRunOut,
)
from app.services import testing_service
from app.services.testing_service import case_detail_dict

router = APIRouter(prefix="/projects/{project_id}/test-cases", tags=["testing"])

admin_or_manager = require_roles("admin", "manager")


@router.get("", response_model=list[TestCaseOut])
def list_cases(
    project_id: int,
    test_type: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return testing_service.list_cases(db, project_id, test_type=test_type)


@router.post("", response_model=TestCaseDetailOut, status_code=201)
def create_case(
    project_id: int,
    body: TestCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    case = testing_service.create_case(db, project_id, body, changed_by=current_user.id)
    return case_detail_dict(case)


@router.get("/{case_id}", response_model=TestCaseDetailOut)
def get_case(
    project_id: int,
    case_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    case = testing_service.get_case(db, project_id, case_id, with_runs=True)
    return case_detail_dict(case)


@router.patch("/{case_id}", response_model=TestCaseDetailOut)
def update_case(
    project_id: int,
    case_id: int,
    body: TestCaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    case = testing_service.update_case(
        db, project_id, case_id, body, changed_by=current_user.id
    )
    return case_detail_dict(case)


@router.patch("/{case_id}/deactivate", status_code=204)
def deactivate_case(
    project_id: int,
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    testing_service.deactivate_case(db, project_id, case_id, changed_by=current_user.id)


@router.post("/{case_id}/runs", response_model=TestRunOut, status_code=201)
def add_run(
    project_id: int,
    case_id: int,
    body: TestRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return testing_service.add_run(db, project_id, case_id, body, tester_id=current_user.id)
