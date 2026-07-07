"""일정 관리(WBS, 마일스톤) 서비스."""
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models import Milestone, User, WbsItem
from app.models.change_log import ACTION_CREATE, ACTION_DEACTIVATE, ACTION_UPDATE
from app.models.milestone import MS_STATUS_ACHIEVED, MS_STATUS_PENDING
from app.models.wbs_item import WBS_STATUS_DONE
from app.schemas.schedule import (
    MilestoneCreate,
    MilestoneUpdate,
    WbsCreate,
    WbsUpdate,
)
from app.services import change_log_service, project_service, user_service

logger = get_logger(__name__)

# 담당자 본인(member)이 수정할 수 있는 필드 (REQ-WBS-008)
ASSIGNEE_EDITABLE_FIELDS = {"progress", "status"}


# ---------- WBS ----------

def get_wbs_item(db: Session, project_id: int, item_id: int) -> WbsItem:
    item = db.scalar(
        select(WbsItem)
        .where(WbsItem.id == item_id, WbsItem.project_id == project_id)
        .options(selectinload(WbsItem.assignee))
    )
    if not item or not item.is_active:
        raise NotFoundError("WBS 항목을 찾을 수 없습니다.")
    return item


def list_wbs(db: Session, project_id: int) -> list[dict]:
    """활성 WBS 항목을 계층 순서(부모 → 자식)로 반환한다. depth 포함."""
    project_service.get_project(db, project_id)
    items = db.scalars(
        select(WbsItem)
        .where(WbsItem.project_id == project_id, WbsItem.is_active.is_(True))
        .options(selectinload(WbsItem.assignee))
        .order_by(WbsItem.sort_order, WbsItem.id)
    ).all()

    children: dict[int | None, list[WbsItem]] = {}
    active_ids = {item.id for item in items}
    for item in items:
        # 부모가 비활성인 경우 최상위로 취급
        key = item.parent_id if item.parent_id in active_ids else None
        children.setdefault(key, []).append(item)

    result: list[dict] = []

    def walk(parent_id: int | None, depth: int) -> None:
        for item in children.get(parent_id, []):
            result.append(_wbs_to_dict(item, depth))
            walk(item.id, depth + 1)

    walk(None, 0)
    return result


def _wbs_to_dict(item: WbsItem, depth: int) -> dict:
    return {
        "id": item.id,
        "parent_id": item.parent_id,
        "name": item.name,
        "assignee_id": item.assignee_id,
        "assignee_name": item.assignee.name if item.assignee else None,
        "start_date": item.start_date,
        "end_date": item.end_date,
        "progress": item.progress,
        "status": item.status,
        "sort_order": item.sort_order,
        "depth": depth,
        "is_delayed": item.is_delayed,
    }


def _validate_parent(
    db: Session, project_id: int, parent_id: int, *, item_id: int | None = None
) -> None:
    """parent 유효성: 같은 프로젝트의 활성 항목, 자기 자신·순환 참조 금지."""
    if item_id is not None and parent_id == item_id:
        raise AppError("자기 자신을 상위 항목으로 지정할 수 없습니다.", code="INVALID_PARENT")

    parent = db.scalar(
        select(WbsItem).where(
            WbsItem.id == parent_id,
            WbsItem.project_id == project_id,
            WbsItem.is_active.is_(True),
        )
    )
    if not parent:
        raise NotFoundError("상위 WBS 항목을 찾을 수 없습니다.")

    # 순환 참조 검사: 새 parent의 조상 중에 자기 자신이 있으면 안 된다
    if item_id is not None:
        cursor: WbsItem | None = parent
        while cursor is not None and cursor.parent_id is not None:
            if cursor.parent_id == item_id:
                raise AppError(
                    "하위 항목을 상위 항목으로 지정할 수 없습니다. (순환 참조)",
                    code="CIRCULAR_PARENT",
                )
            cursor = db.get(WbsItem, cursor.parent_id)


def create_wbs(db: Session, project_id: int, data: WbsCreate, *, changed_by: int) -> dict:
    project_service.get_project(db, project_id)
    if data.parent_id is not None:
        _validate_parent(db, project_id, data.parent_id)
    if data.assignee_id is not None:
        user_service.get_user(db, data.assignee_id)

    payload = data.model_dump()
    # REQ-WBS-007: 진척률 100 → 완료 처리
    if payload["progress"] == 100:
        payload["status"] = WBS_STATUS_DONE

    item = WbsItem(project_id=project_id, **payload)
    db.add(item)
    db.flush()
    change_log_service.record(
        db,
        entity_type="wbs",
        entity_id=item.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(item),
    )
    db.commit()
    logger.info("wbs created: id=%s project_id=%s", item.id, project_id)
    return _wbs_to_dict(get_wbs_item(db, project_id, item.id), 0)


def update_wbs(
    db: Session, project_id: int, item_id: int, data: WbsUpdate, *, current_user: User
) -> dict:
    item = get_wbs_item(db, project_id, item_id)
    payload = data.model_dump(exclude_unset=True)

    # 권한: admin/manager 전체, 담당자 본인은 진척률·상태만 (REQ-WBS-008)
    if current_user.role not in ("admin", "manager"):
        if item.assignee_id != current_user.id:
            raise ForbiddenError("담당자 본인만 수정할 수 있습니다.", code="NOT_ASSIGNEE")
        illegal = set(payload) - ASSIGNEE_EDITABLE_FIELDS
        if illegal:
            raise ForbiddenError(
                "담당자는 진척률과 상태만 수정할 수 있습니다.", code="FIELD_NOT_ALLOWED"
            )

    if "parent_id" in payload and payload["parent_id"] is not None:
        _validate_parent(db, project_id, payload["parent_id"], item_id=item_id)
    if "assignee_id" in payload and payload["assignee_id"] is not None:
        user_service.get_user(db, payload["assignee_id"])

    before = change_log_service.snapshot(item)
    for field, value in payload.items():
        setattr(item, field, value)
    # REQ-WBS-007: 진척률 100 → 완료 처리
    if item.progress == 100:
        item.status = WBS_STATUS_DONE

    change_log_service.record(
        db,
        entity_type="wbs",
        entity_id=item.id,
        action=ACTION_UPDATE,
        changed_by=current_user.id,
        before_data=before,
        after_data=change_log_service.snapshot(item),
    )
    db.commit()
    return _wbs_to_dict(get_wbs_item(db, project_id, item_id), 0)


def deactivate_wbs(db: Session, project_id: int, item_id: int, *, changed_by: int) -> None:
    """항목과 모든 하위 항목을 논리 삭제한다 (REQ-WBS-006)."""
    item = get_wbs_item(db, project_id, item_id)

    all_items = db.scalars(
        select(WbsItem).where(
            WbsItem.project_id == project_id, WbsItem.is_active.is_(True)
        )
    ).all()
    children_map: dict[int, list[WbsItem]] = {}
    for i in all_items:
        if i.parent_id is not None:
            children_map.setdefault(i.parent_id, []).append(i)

    targets: list[WbsItem] = []

    def collect(node: WbsItem) -> None:
        targets.append(node)
        for child in children_map.get(node.id, []):
            collect(child)

    collect(item)
    for target in targets:
        before = change_log_service.snapshot(target)
        target.is_active = False
        change_log_service.record(
            db,
            entity_type="wbs",
            entity_id=target.id,
            action=ACTION_DEACTIVATE,
            changed_by=changed_by,
            before_data=before,
            after_data=change_log_service.snapshot(target),
        )
    db.commit()
    logger.info(
        "wbs deactivated: id=%s (+%s children)", item_id, len(targets) - 1
    )


# ---------- 마일스톤 ----------

def get_milestone(db: Session, project_id: int, ms_id: int) -> Milestone:
    ms = db.scalar(
        select(Milestone).where(
            Milestone.id == ms_id, Milestone.project_id == project_id
        )
    )
    if not ms or not ms.is_active:
        raise NotFoundError("마일스톤을 찾을 수 없습니다.")
    return ms


def list_milestones(db: Session, project_id: int) -> list[Milestone]:
    project_service.get_project(db, project_id)
    return list(
        db.scalars(
            select(Milestone)
            .where(Milestone.project_id == project_id, Milestone.is_active.is_(True))
            .order_by(Milestone.due_date, Milestone.id)
        ).all()
    )


def create_milestone(
    db: Session, project_id: int, data: MilestoneCreate, *, changed_by: int
) -> Milestone:
    project_service.get_project(db, project_id)
    ms = Milestone(project_id=project_id, **data.model_dump())
    db.add(ms)
    db.flush()
    change_log_service.record(
        db,
        entity_type="milestone",
        entity_id=ms.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(ms),
    )
    db.commit()
    db.refresh(ms)
    logger.info("milestone created: id=%s project_id=%s", ms.id, project_id)
    return ms


def update_milestone(
    db: Session, project_id: int, ms_id: int, data: MilestoneUpdate, *, changed_by: int
) -> Milestone:
    ms = get_milestone(db, project_id, ms_id)
    before = change_log_service.snapshot(ms)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ms, field, value)
    change_log_service.record(
        db,
        entity_type="milestone",
        entity_id=ms.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(ms),
    )
    db.commit()
    db.refresh(ms)
    return ms


def achieve_milestone(
    db: Session, project_id: int, ms_id: int, *, changed_by: int
) -> Milestone:
    """달성 처리 (REQ-MS-002)."""
    ms = get_milestone(db, project_id, ms_id)
    if ms.status == MS_STATUS_ACHIEVED:
        raise AppError("이미 달성된 마일스톤입니다.", code="ALREADY_ACHIEVED")
    before = change_log_service.snapshot(ms)
    ms.status = MS_STATUS_ACHIEVED
    ms.achieved_date = date.today()
    change_log_service.record(
        db,
        entity_type="milestone",
        entity_id=ms.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(ms),
    )
    db.commit()
    db.refresh(ms)
    logger.info("milestone achieved: id=%s", ms.id)
    return ms


def deactivate_milestone(
    db: Session, project_id: int, ms_id: int, *, changed_by: int
) -> None:
    ms = get_milestone(db, project_id, ms_id)
    before = change_log_service.snapshot(ms)
    ms.is_active = False
    change_log_service.record(
        db,
        entity_type="milestone",
        entity_id=ms.id,
        action=ACTION_DEACTIVATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(ms),
    )
    db.commit()


# ---------- 일정 요약 ----------

def schedule_summary(db: Session, project_id: int) -> dict:
    """REQ-SCH-001: 전체 진척률(활성 WBS 평균)과 지연 항목 수."""
    project_service.get_project(db, project_id)
    wbs_items = db.scalars(
        select(WbsItem).where(
            WbsItem.project_id == project_id, WbsItem.is_active.is_(True)
        )
    ).all()
    milestones = db.scalars(
        select(Milestone).where(
            Milestone.project_id == project_id, Milestone.is_active.is_(True)
        )
    ).all()

    progress = (
        round(sum(i.progress for i in wbs_items) / len(wbs_items), 1)
        if wbs_items
        else 0.0
    )
    pending = [m for m in milestones if m.status == MS_STATUS_PENDING]
    return {
        "progress": progress,
        "wbs_total": len(wbs_items),
        "wbs_delayed": sum(1 for i in wbs_items if i.is_delayed),
        "milestone_total": len(milestones),
        "milestone_delayed": sum(1 for m in pending if m.is_delayed),
    }
