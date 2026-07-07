from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.schemas.schedule import (
    MilestoneCreate,
    MilestoneOut,
    MilestoneUpdate,
    ScheduleSummary,
    WbsCreate,
    WbsOut,
    WbsUpdate,
)
from app.services import schedule_service

router = APIRouter(prefix="/projects/{project_id}", tags=["schedule"])

admin_or_manager = require_roles("admin", "manager")


# ---------- WBS ----------

@router.get("/wbs", response_model=list[WbsOut])
def list_wbs(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return schedule_service.list_wbs(db, project_id)


@router.post("/wbs", response_model=WbsOut, status_code=201)
def create_wbs(
    project_id: int,
    body: WbsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return schedule_service.create_wbs(db, project_id, body, changed_by=current_user.id)


@router.patch("/wbs/{item_id}", response_model=WbsOut)
def update_wbs(
    project_id: int,
    item_id: int,
    body: WbsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 세부 권한(담당자 본인은 진척률·상태만)은 서비스 계층에서 검증
    return schedule_service.update_wbs(
        db, project_id, item_id, body, current_user=current_user
    )


@router.patch("/wbs/{item_id}/deactivate", status_code=204)
def deactivate_wbs(
    project_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    schedule_service.deactivate_wbs(db, project_id, item_id, changed_by=current_user.id)


# ---------- 마일스톤 ----------

@router.get("/milestones", response_model=list[MilestoneOut])
def list_milestones(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return schedule_service.list_milestones(db, project_id)


@router.post("/milestones", response_model=MilestoneOut, status_code=201)
def create_milestone(
    project_id: int,
    body: MilestoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return schedule_service.create_milestone(
        db, project_id, body, changed_by=current_user.id
    )


@router.patch("/milestones/{ms_id}", response_model=MilestoneOut)
def update_milestone(
    project_id: int,
    ms_id: int,
    body: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return schedule_service.update_milestone(
        db, project_id, ms_id, body, changed_by=current_user.id
    )


@router.patch("/milestones/{ms_id}/achieve", response_model=MilestoneOut)
def achieve_milestone(
    project_id: int,
    ms_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return schedule_service.achieve_milestone(
        db, project_id, ms_id, changed_by=current_user.id
    )


@router.patch("/milestones/{ms_id}/deactivate", status_code=204)
def deactivate_milestone(
    project_id: int,
    ms_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    schedule_service.deactivate_milestone(
        db, project_id, ms_id, changed_by=current_user.id
    )


# ---------- 일정 요약 ----------

@router.get("/schedule/summary", response_model=ScheduleSummary)
def schedule_summary(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return schedule_service.schedule_summary(db, project_id)
