"""사용자 관리 서비스."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.core.security import hash_password
from app.models import User
from app.models.change_log import ACTION_CREATE, ACTION_DEACTIVATE, ACTION_UPDATE
from app.schemas.user import UserCreate, UserUpdate
from app.services import change_log_service

logger = get_logger(__name__)


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if not user:
        raise NotFoundError("사용자를 찾을 수 없습니다.")
    return user


def list_users(db: Session, *, page: int = 1, size: int = 20) -> tuple[list[User], int]:
    total = db.scalar(select(func.count()).select_from(User)) or 0
    rows = db.scalars(
        select(User).order_by(User.id).offset((page - 1) * size).limit(size)
    ).all()
    return list(rows), total


def create_user(db: Session, data: UserCreate, *, changed_by: int) -> User:
    exists = db.scalar(select(User.id).where(User.email == data.email))
    if exists:
        raise ConflictError("이미 등록된 이메일입니다.", code="EMAIL_DUPLICATED")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        name=data.name,
        role=data.role,
    )
    db.add(user)
    db.flush()
    change_log_service.record(
        db,
        entity_type="user",
        entity_id=user.id,
        action=ACTION_CREATE,
        changed_by=changed_by,
        after_data=change_log_service.snapshot(user),
    )
    db.commit()
    db.refresh(user)
    logger.info("user created: id=%s email=%s", user.id, user.email)
    return user


def update_user(db: Session, user_id: int, data: UserUpdate, *, changed_by: int) -> User:
    user = get_user(db, user_id)
    before = change_log_service.snapshot(user)

    if data.name is not None:
        user.name = data.name
    if data.role is not None:
        user.role = data.role
    if data.password is not None:
        user.password_hash = hash_password(data.password)

    change_log_service.record(
        db,
        entity_type="user",
        entity_id=user.id,
        action=ACTION_UPDATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(user),
    )
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: int, *, changed_by: int) -> User:
    user = get_user(db, user_id)
    before = change_log_service.snapshot(user)
    user.is_active = False
    change_log_service.record(
        db,
        entity_type="user",
        entity_id=user.id,
        action=ACTION_DEACTIVATE,
        changed_by=changed_by,
        before_data=before,
        after_data=change_log_service.snapshot(user),
    )
    db.commit()
    db.refresh(user)
    logger.info("user deactivated: id=%s", user.id)
    return user
