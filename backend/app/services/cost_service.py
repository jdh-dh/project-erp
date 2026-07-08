"""프로젝트 비용 서비스."""
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models import ProjectCost
from app.models.change_log import ACTION_CREATE, ACTION_DEACTIVATE, ACTION_UPDATE
from app.schemas.cost import CostCreate, CostUpdate
from app.services import change_log_service, project_service

logger = get_logger(__name__)


def cost_to_dict(cost: ProjectCost) -> dict:
    return {
        "id": cost.id,
        "cost_date": cost.cost_date,
        "category": cost.category,
        "item": cost.item,
        "amount": cost.amount,
        "note": cost.note,
        "created_by": cost.created_by,
        "creator_name": cost.creator.name,
    }


def get_cost(db: Session, project_id: int, cost_id: int) -> ProjectCost:
    cost = db.scalar(
        select(ProjectCost)
        .where(ProjectCost.id == cost_id, ProjectCost.project_id == project_id)
        .options(selectinload(ProjectCost.creator))
    )
    if not cost or not cost.is_active:
        raise NotFoundError("비용 항목을 찾을 수 없습니다.")
    return cost


def list_costs(
    db: Session, project_id: int, *, category: str | None = None
) -> list[ProjectCost]:
    project_service.get_project(db, project_id)
    query = (
        select(ProjectCost)
        .where(ProjectCost.project_id == project_id, ProjectCost.is_active.is_(True))
        .options(selectinload(ProjectCost.creator))
        .order_by(ProjectCost.cost_date.desc(), ProjectCost.id.desc())
    )
    if category:
        query = query.where(ProjectCost.category == category)
    return list(db.scalars(query).all())


def create_cost(db: Session, project_id: int, data: CostCreate, *, created_by: int) -> ProjectCost:
    project_service.get_project(db, project_id)
    cost = ProjectCost(project_id=project_id, created_by=created_by, **data.model_dump())
    db.add(cost)
    db.flush()
    change_log_service.record(
        db,
        entity_type="project_cost",
        entity_id=cost.id,
        action=ACTION_CREATE,
        changed_by=created_by,
        after_data=change_log_service.snapshot(cost),
    )
    db.commit()
    logger.info("cost created: id=%s project_id=%s amount=%s", cost.id, project_id, cost.amount)
    return get_cost(db, project_id, cost.id)


def update_cost(
    db: Session, project_id: int, cost_id: int, data: CostUpdate, *, changed_by: int
) -> ProjectCost:
    cost = get_cost(db, project_id, cost_id)
    before = change_log_service.snapshot(cost)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cost, field, value)
    change_log_service.record(
        db,
        entity_type="project_cost",
        entity_id=cost.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(cost),
    )
    db.commit()
    return get_cost(db, project_id, cost_id)


def deactivate_cost(db: Session, project_id: int, cost_id: int, *, changed_by: int) -> None:
    cost = get_cost(db, project_id, cost_id)
    before = change_log_service.snapshot(cost)
    cost.is_active = False
    change_log_service.record(
        db,
        entity_type="project_cost",
        entity_id=cost.id,
        action=ACTION_DEACTIVATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(cost),
    )
    db.commit()


def cost_summary(db: Session, project_id: int) -> dict:
    """총액·분류별 합계 (비활성 제외, REQ-COST-003)."""
    project_service.get_project(db, project_id)
    costs = db.scalars(
        select(ProjectCost).where(
            ProjectCost.project_id == project_id, ProjectCost.is_active.is_(True)
        )
    ).all()
    by_category: dict[str, Decimal] = {}
    total = Decimal(0)
    for cost in costs:
        by_category[cost.category] = by_category.get(cost.category, Decimal(0)) + cost.amount
        total += cost.amount
    return {"total": total, "by_category": by_category}
