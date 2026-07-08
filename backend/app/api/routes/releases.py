from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models import User
from app.schemas.release import ReleaseCreate, ReleaseOut, ReleaseUpdate
from app.services import release_service
from app.services.release_service import release_to_dict

router = APIRouter(prefix="/projects/{project_id}/releases", tags=["releases"])

admin_or_manager = require_roles("admin", "manager")


@router.get("", response_model=list[ReleaseOut])
def list_releases(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return [release_to_dict(r) for r in release_service.list_releases(db, project_id)]


@router.post("", response_model=ReleaseOut, status_code=201)
def create_release(
    project_id: int,
    body: ReleaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    release = release_service.create_release(db, project_id, body, created_by=current_user.id)
    return release_to_dict(release)


@router.patch("/{release_id}", response_model=ReleaseOut)
def update_release(
    project_id: int,
    release_id: int,
    body: ReleaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    release = release_service.update_release(
        db, project_id, release_id, body, changed_by=current_user.id
    )
    return release_to_dict(release)


@router.patch("/{release_id}/deactivate", status_code=204)
def deactivate_release(
    project_id: int,
    release_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_or_manager),
):
    release_service.deactivate_release(db, project_id, release_id, changed_by=current_user.id)
