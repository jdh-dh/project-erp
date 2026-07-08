from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.issue import (
    IssueCreate,
    IssueDetailOut,
    IssueOut,
    IssueStatusUpdate,
    IssueUpdate,
)
from app.services import issue_service
from app.services.issue_service import issue_to_dict

router = APIRouter(prefix="/projects/{project_id}/issues", tags=["issues"])


@router.get("", response_model=list[IssueOut])
def list_issues(
    project_id: int,
    status: str | None = None,
    issue_type: str | None = None,
    assignee_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    issues = issue_service.list_issues(
        db, project_id, status=status, issue_type=issue_type, assignee_id=assignee_id
    )
    return [issue_to_dict(i) for i in issues]


@router.post("", response_model=IssueDetailOut, status_code=201)
def create_issue(
    project_id: int,
    body: IssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = issue_service.create_issue(db, project_id, body, reporter=current_user)
    return issue_to_dict(issue, detail=True)


@router.get("/{issue_id}", response_model=IssueDetailOut)
def get_issue(
    project_id: int,
    issue_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return issue_to_dict(issue_service.get_issue(db, project_id, issue_id), detail=True)


@router.patch("/{issue_id}", response_model=IssueDetailOut)
def update_issue(
    project_id: int,
    issue_id: int,
    body: IssueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 세부 권한(admin/manager/담당자)은 서비스 계층에서 검증
    issue = issue_service.update_issue(db, project_id, issue_id, body, current_user=current_user)
    return issue_to_dict(issue, detail=True)


@router.patch("/{issue_id}/status", response_model=IssueDetailOut)
def change_status(
    project_id: int,
    issue_id: int,
    body: IssueStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = issue_service.change_status(
        db, project_id, issue_id, body, current_user=current_user
    )
    return issue_to_dict(issue, detail=True)
