from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.schemas.software import (
    BuildCreate,
    BuildOut,
    DeploymentCreate,
    DeploymentOut,
    ModuleCreate,
    ModuleDetailOut,
    ModuleOut,
    ModuleUpdate,
    VersionCreate,
    VersionDetailOut,
    VersionOut,
    VersionUpdate,
)
from app.services import software_service
from app.services.software_service import module_detail_dict, version_detail_dict

router = APIRouter(prefix="/projects/{project_id}/sw", tags=["software"])

admin_or_manager = require_roles("admin", "manager")


@router.get("/modules", response_model=list[ModuleOut])
def list_modules(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return software_service.list_modules(db, project_id)


@router.post("/modules", response_model=ModuleDetailOut, status_code=201)
def create_module(
    project_id: int,
    body: ModuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return software_service.create_module(db, project_id, body, changed_by=current_user.id)


@router.get("/modules/{module_id}", response_model=ModuleDetailOut)
def get_module(
    project_id: int,
    module_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    module = software_service.get_module(db, project_id, module_id, with_versions=True)
    return module_detail_dict(module)


@router.patch("/modules/{module_id}", response_model=ModuleDetailOut)
def update_module(
    project_id: int,
    module_id: int,
    body: ModuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return software_service.update_module(
        db, project_id, module_id, body, changed_by=current_user.id
    )


@router.patch("/modules/{module_id}/deactivate", status_code=204)
def deactivate_module(
    project_id: int,
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    software_service.deactivate_module(
        db, project_id, module_id, changed_by=current_user.id
    )


@router.post("/modules/{module_id}/versions", response_model=VersionOut, status_code=201)
def create_version(
    project_id: int,
    module_id: int,
    body: VersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return software_service.create_version(
        db, project_id, module_id, body, changed_by=current_user.id
    )


@router.get("/modules/{module_id}/versions/{version_id}", response_model=VersionDetailOut)
def get_version(
    project_id: int,
    module_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    version = software_service.get_version(
        db, project_id, module_id, version_id, with_detail=True
    )
    return version_detail_dict(version)


@router.patch("/modules/{module_id}/versions/{version_id}", response_model=VersionOut)
def update_version(
    project_id: int,
    module_id: int,
    version_id: int,
    body: VersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return software_service.update_version(
        db, project_id, module_id, version_id, body, changed_by=current_user.id
    )


@router.patch(
    "/modules/{module_id}/versions/{version_id}/release", response_model=VersionOut
)
def release_version(
    project_id: int,
    module_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return software_service.release_version(
        db, project_id, module_id, version_id, changed_by=current_user.id
    )


@router.post(
    "/modules/{module_id}/versions/{version_id}/builds",
    response_model=BuildOut,
    status_code=201,
)
def add_build(
    project_id: int,
    module_id: int,
    version_id: int,
    body: BuildCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return software_service.add_build(
        db, project_id, module_id, version_id, body, changed_by=current_user.id
    )


@router.post(
    "/modules/{module_id}/versions/{version_id}/deployments",
    response_model=DeploymentOut,
    status_code=201,
)
def add_deployment(
    project_id: int,
    module_id: int,
    version_id: int,
    body: DeploymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    return software_service.add_deployment(
        db, project_id, module_id, version_id, body, changed_by=current_user.id
    )
