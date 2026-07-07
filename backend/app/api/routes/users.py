from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models import User
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])

admin_only = require_roles("admin")
admin_or_manager = require_roles("admin", "manager")


@router.get("", response_model=Page[UserOut])
def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(admin_or_manager),
):
    items, total = user_service.list_users(db, page=page, size=size)
    return Page(items=items, total=total, page=page, size=size)


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    return user_service.create_user(db, body, changed_by=current_user.id)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(admin_or_manager),
):
    return user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    return user_service.update_user(db, user_id, body, changed_by=current_user.id)


@router.patch("/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_only),
):
    return user_service.deactivate_user(db, user_id, changed_by=current_user.id)
