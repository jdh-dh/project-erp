"""이슈 관리 서비스."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models import Issue, User
from app.models.change_log import ACTION_CREATE, ACTION_STATUS_CHANGE, ACTION_UPDATE
from app.models.issue import ISSUE_STATUS_RESOLVED, ISSUE_STATUS_TRANSITIONS
from app.schemas.issue import IssueCreate, IssueStatusUpdate, IssueUpdate
from app.services import change_log_service, project_service, user_service

logger = get_logger(__name__)


def issue_to_dict(issue: Issue, *, detail: bool = False) -> dict:
    data = {
        "id": issue.id,
        "issue_type": issue.issue_type,
        "title": issue.title,
        "severity": issue.severity,
        "status": issue.status,
        "reporter_id": issue.reporter_id,
        "reporter_name": issue.reporter.name,
        "assignee_id": issue.assignee_id,
        "assignee_name": issue.assignee.name if issue.assignee else None,
        "resolved_date": issue.resolved_date,
        "created_at": issue.created_at,
    }
    if detail:
        data.update(
            description=issue.description,
            cause_analysis=issue.cause_analysis,
            resolution=issue.resolution,
        )
    return data


def get_issue(db: Session, project_id: int, issue_id: int) -> Issue:
    issue = db.scalar(
        select(Issue)
        .where(Issue.id == issue_id, Issue.project_id == project_id)
        .options(selectinload(Issue.reporter), selectinload(Issue.assignee))
    )
    if not issue or not issue.is_active:
        raise NotFoundError("이슈를 찾을 수 없습니다.")
    return issue


def list_issues(
    db: Session,
    project_id: int,
    *,
    status: str | None = None,
    issue_type: str | None = None,
    assignee_id: int | None = None,
) -> list[Issue]:
    project_service.get_project(db, project_id)
    query = (
        select(Issue)
        .where(Issue.project_id == project_id, Issue.is_active.is_(True))
        .options(selectinload(Issue.reporter), selectinload(Issue.assignee))
        .order_by(Issue.id.desc())
    )
    if status:
        query = query.where(Issue.status == status)
    if issue_type:
        query = query.where(Issue.issue_type == issue_type)
    if assignee_id is not None:
        query = query.where(Issue.assignee_id == assignee_id)
    return list(db.scalars(query).all())


def create_issue(db: Session, project_id: int, data: IssueCreate, *, reporter: User) -> Issue:
    """이슈 등록. 모든 로그인 사용자 가능, 등록자 자동 기록 (REQ-ISS-006)."""
    project_service.get_project(db, project_id)
    if data.assignee_id is not None:
        user_service.get_user(db, data.assignee_id)

    issue = Issue(project_id=project_id, reporter_id=reporter.id, **data.model_dump())
    db.add(issue)
    db.flush()
    change_log_service.record(
        db,
        entity_type="issue",
        entity_id=issue.id,
        action=ACTION_CREATE,
        changed_by=reporter.id,
        after_data=change_log_service.snapshot(issue),
    )
    db.commit()
    logger.info("issue created: id=%s project_id=%s type=%s", issue.id, project_id, issue.issue_type)
    return get_issue(db, project_id, issue.id)


def _check_edit_permission(issue: Issue, current_user: User) -> None:
    """이슈 수정 권한: admin/manager 또는 담당자 (REQ-ISS-007)."""
    if current_user.role in ("admin", "manager"):
        return
    if issue.assignee_id == current_user.id:
        return
    raise ForbiddenError(
        "이슈 수정은 관리자 또는 담당자만 가능합니다.", code="NOT_ISSUE_EDITOR"
    )


def update_issue(
    db: Session, project_id: int, issue_id: int, data: IssueUpdate, *, current_user: User
) -> Issue:
    issue = get_issue(db, project_id, issue_id)
    _check_edit_permission(issue, current_user)

    payload = data.model_dump(exclude_unset=True)
    if "assignee_id" in payload and payload["assignee_id"] is not None:
        user_service.get_user(db, payload["assignee_id"])

    before = change_log_service.snapshot(issue)
    for field, value in payload.items():
        setattr(issue, field, value)
    change_log_service.record(
        db,
        entity_type="issue",
        entity_id=issue.id,
        action=ACTION_UPDATE,
        changed_by=current_user.id,
        before_data=before,
        after_data=change_log_service.snapshot(issue),
    )
    db.commit()
    return get_issue(db, project_id, issue_id)


def change_status(
    db: Session, project_id: int, issue_id: int, data: IssueStatusUpdate, *, current_user: User
) -> Issue:
    """상태 변경. RESOLVED는 조치 결과 필수 (REQ-ISS-004, 005)."""
    issue = get_issue(db, project_id, issue_id)
    _check_edit_permission(issue, current_user)

    allowed = ISSUE_STATUS_TRANSITIONS.get(issue.status, ())
    if data.status not in allowed:
        raise AppError(
            f"'{issue.status}' 상태에서 '{data.status}' 상태로 변경할 수 없습니다.",
            code="INVALID_STATUS_TRANSITION",
        )

    before = change_log_service.snapshot(issue)
    if data.status == ISSUE_STATUS_RESOLVED:
        resolution = data.resolution or issue.resolution
        if not resolution:
            raise AppError(
                "RESOLVED 처리에는 조치 결과(resolution)가 필요합니다.",
                code="RESOLUTION_REQUIRED",
            )
        issue.resolution = resolution
        issue.resolved_date = date.today()
    elif data.resolution is not None:
        issue.resolution = data.resolution

    issue.status = data.status
    change_log_service.record(
        db,
        entity_type="issue",
        entity_id=issue.id,
        action=ACTION_STATUS_CHANGE,
        changed_by=current_user.id,
        before_data=before,
        after_data=change_log_service.snapshot(issue),
    )
    db.commit()
    logger.info("issue status changed: id=%s %s→%s", issue_id, before["status"], data.status)
    return get_issue(db, project_id, issue_id)
