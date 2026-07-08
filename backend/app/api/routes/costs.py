from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.schemas.cost import CostCreate, CostOut, CostSummary, CostUpdate
from app.services import cost_service
from app.services.cost_service import cost_to_dict

router = APIRouter(prefix="/projects/{project_id}/costs", tags=["costs"])

admin_or_manager = require_roles("admin", "manager")


@router.get("", response_model=list[CostOut])
def list_costs(
    project_id: int,
    category: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [cost_to_dict(c) for c in cost_service.list_costs(db, project_id, category=category)]


@router.get("/summary", response_model=CostSummary)
def cost_summary(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return cost_service.cost_summary(db, project_id)


@router.post("", response_model=CostOut, status_code=201)
def create_cost(
    project_id: int,
    body: CostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return cost_to_dict(cost_service.create_cost(db, project_id, body, created_by=current_user.id))


@router.patch("/{cost_id}", response_model=CostOut)
def update_cost(
    project_id: int,
    cost_id: int,
    body: CostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return cost_to_dict(
        cost_service.update_cost(db, project_id, cost_id, body, changed_by=current_user.id)
    )


@router.patch("/{cost_id}/deactivate", status_code=204)
def deactivate_cost(
    project_id: int,
    cost_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    cost_service.deactivate_cost(db, project_id, cost_id, changed_by=current_user.id)
