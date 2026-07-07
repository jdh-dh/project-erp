"""프로젝트 관리 서비스."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.core.logging import get_logger
from app.models import Contract, Project, ProjectMember, User
from app.models.change_log import ACTION_CREATE, ACTION_STATUS_CHANGE, ACTION_UPDATE
from app.models.project import STATUS_TRANSITIONS
from app.schemas.project import (
    ContractCreate,
    ContractUpdate,
    MembersSet,
    ProjectCreate,
    ProjectUpdate,
)
from app.services import change_log_service, customer_service, user_service

logger = get_logger(__name__)


def get_project(db: Session, project_id: int, *, with_detail: bool = False) -> Project:
    query = select(Project).where(Project.id == project_id)
    if with_detail:
        query = query.options(
            selectinload(Project.members).selectinload(ProjectMember.user),
            selectinload(Project.contracts),
            selectinload(Project.customer),
            selectinload(Project.manager),
        )
    project = db.scalar(query)
    if not project:
        raise NotFoundError("프로젝트를 찾을 수 없습니다.")
    return project


def list_projects(
    db: Session,
    *,
    status: str | None = None,
    customer_id: int | None = None,
    q: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Project], int]:
    query = select(Project).options(
        selectinload(Project.customer), selectinload(Project.manager)
    )
    if status:
        query = query.where(Project.status == status)
    if customer_id is not None:
        query = query.where(Project.customer_id == customer_id)
    if q:
        query = query.where(
            or_(Project.name.ilike(f"%{q}%"), Project.code.ilike(f"%{q}%"))
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(Project.id.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return list(rows), total


def create_project(db: Session, data: ProjectCreate, *, changed_by: int) -> Project:
    if db.scalar(select(Project.id).where(Project.code == data.code)):
        raise ConflictError("이미 사용 중인 프로젝트 코드입니다.", code="PROJECT_CODE_DUPLICATED")

    # FK 유효성 검증 (없으면 NotFoundError)
    customer_service.get_customer(db, data.customer_id)
    user_service.get_user(db, data.manager_id)

    project = Project(**data.model_dump())
    db.add(project)
    db.flush()
    change_log_service.record(
        db,
        entity_type="project",
        entity_id=project.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(project),
    )
    db.commit()
    logger.info("project created: id=%s code=%s", project.id, project.code)
    return get_project(db, project.id, with_detail=True)


def update_project(
    db: Session, project_id: int, data: ProjectUpdate, *, changed_by: int
) -> Project:
    project = get_project(db, project_id)
    before = change_log_service.snapshot(project)

    payload = data.model_dump(exclude_unset=True)
    if "customer_id" in payload:
        customer_service.get_customer(db, payload["customer_id"])
    if "manager_id" in payload:
        user_service.get_user(db, payload["manager_id"])
    for field, value in payload.items():
        setattr(project, field, value)

    change_log_service.record(
        db,
        entity_type="project",
        entity_id=project.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(project),
    )
    db.commit()
    return get_project(db, project_id, with_detail=True)


def change_status(db: Session, project_id: int, new_status: str, *, changed_by: int) -> Project:
    """상태 전이 규칙(api.md 6절)을 검증한 후 상태를 변경한다."""
    project = get_project(db, project_id)
    allowed = STATUS_TRANSITIONS.get(project.status, ())
    if new_status not in allowed:
        raise AppError(
            f"'{project.status}' 상태에서 '{new_status}' 상태로 변경할 수 없습니다.",
            code="INVALID_STATUS_TRANSITION",
        )
    before = change_log_service.snapshot(project)
    project.status = new_status
    change_log_service.record(
        db,
        entity_type="project",
        entity_id=project.id,
        action=ACTION_STATUS_CHANGE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(project),
    )
    db.commit()
    logger.info("project status changed: id=%s %s→%s", project.id, before["status"], new_status)
    return get_project(db, project_id, with_detail=True)


def set_members(db: Session, project_id: int, data: MembersSet, *, changed_by: int) -> Project:
    """참여자를 일괄 설정한다 (기존 목록을 교체)."""
    project = get_project(db, project_id, with_detail=True)

    user_ids = [m.user_id for m in data.members]
    if len(user_ids) != len(set(user_ids)):
        raise AppError("중복된 참여자가 있습니다.", code="DUPLICATED_MEMBER")
    for user_id in user_ids:
        user_service.get_user(db, user_id)

    before = [
        {"user_id": m.user_id, "role": m.role} for m in project.members
    ]
    project.members.clear()
    for m in data.members:
        project.members.append(ProjectMember(user_id=m.user_id, role=m.role))

    change_log_service.record(
        db,
        entity_type="project",
        entity_id=project.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data={"members": before},
        after_data={"members": [m.model_dump() for m in data.members]},
    )
    db.commit()
    return get_project(db, project_id, with_detail=True)


def add_contract(
    db: Session, project_id: int, data: ContractCreate, *, changed_by: int
) -> Contract:
    project = get_project(db, project_id)
    contract = Contract(project_id=project.id, **data.model_dump())
    db.add(contract)
    db.flush()
    change_log_service.record(
        db,
        entity_type="contract",
        entity_id=contract.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(contract),
    )
    db.commit()
    db.refresh(contract)
    logger.info("contract created: id=%s project_id=%s", contract.id, project.id)
    return contract


def update_contract(
    db: Session, project_id: int, contract_id: int, data: ContractUpdate, *, changed_by: int
) -> Contract:
    contract = db.scalar(
        select(Contract).where(
            Contract.id == contract_id, Contract.project_id == project_id
        )
    )
    if not contract:
        raise NotFoundError("계약을 찾을 수 없습니다.")
    before = change_log_service.snapshot(contract)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(contract, field, value)
    change_log_service.record(
        db,
        entity_type="contract",
        entity_id=contract.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(contract),
    )
    db.commit()
    db.refresh(contract)
    return contract
