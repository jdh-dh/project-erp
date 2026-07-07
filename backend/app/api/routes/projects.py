from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import Project, User
from app.schemas.common import Page
from app.schemas.project import (
    ContractCreate,
    ContractOut,
    ContractUpdate,
    MembersSet,
    ProjectCreate,
    ProjectDetailOut,
    ProjectOut,
    ProjectStatusUpdate,
    ProjectUpdate,
)
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])

admin_or_manager = require_roles("admin", "manager")


def _to_out(project: Project) -> dict:
    return {
        "id": project.id,
        "code": project.code,
        "name": project.name,
        "customer_id": project.customer_id,
        "customer_name": project.customer.name,
        "project_type": project.project_type,
        "status": project.status,
        "manager_id": project.manager_id,
        "manager_name": project.manager.name,
        "start_date": project.start_date,
        "end_date": project.end_date,
        "created_at": project.created_at,
    }


def _to_detail_out(project: Project) -> dict:
    data = _to_out(project)
    data["description"] = project.description
    data["members"] = [
        {"id": m.id, "user_id": m.user_id, "role": m.role, "user_name": m.user.name}
        for m in project.members
    ]
    data["contracts"] = [ContractOut.model_validate(c) for c in project.contracts]
    return data


@router.get("", response_model=Page[ProjectOut])
def list_projects(
    status: str | None = None,
    customer_id: int | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    items, total = project_service.list_projects(
        db, status=status, customer_id=customer_id, q=q, page=page, size=size
    )
    return Page(items=[_to_out(p) for p in items], total=total, page=page, size=size)


@router.post("", response_model=ProjectDetailOut, status_code=201)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    project = project_service.create_project(db, body, changed_by=current_user.id)
    return _to_detail_out(project)


@router.get("/{project_id}", response_model=ProjectDetailOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    project = project_service.get_project(db, project_id, with_detail=True)
    return _to_detail_out(project)


@router.patch("/{project_id}", response_model=ProjectDetailOut)
def update_project(
    project_id: int,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    project = project_service.update_project(db, project_id, body, changed_by=current_user.id)
    return _to_detail_out(project)


@router.patch("/{project_id}/status", response_model=ProjectDetailOut)
def change_status(
    project_id: int,
    body: ProjectStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    project = project_service.change_status(
        db, project_id, body.status, changed_by=current_user.id
    )
    return _to_detail_out(project)


@router.put("/{project_id}/members", response_model=ProjectDetailOut)
def set_members(
    project_id: int,
    body: MembersSet,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    project = project_service.set_members(db, project_id, body, changed_by=current_user.id)
    return _to_detail_out(project)


@router.post("/{project_id}/contracts", response_model=ContractOut, status_code=201)
def add_contract(
    project_id: int,
    body: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return project_service.add_contract(db, project_id, body, changed_by=current_user.id)


@router.patch("/{project_id}/contracts/{contract_id}", response_model=ContractOut)
def update_contract(
    project_id: int,
    contract_id: int,
    body: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return project_service.update_contract(
        db, project_id, contract_id, body, changed_by=current_user.id
    )
