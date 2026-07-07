"""초기 admin 계정 생성 스크립트.

사용법: python -m app.initial_data
이미 admin 이메일이 존재하면 아무 것도 하지 않는다.
"""
from sqlalchemy import select

from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User
from app.models.user import ROLE_ADMIN

setup_logging()
logger = get_logger(__name__)


def create_initial_admin() -> None:
    with SessionLocal() as db:
        exists = db.scalar(select(User.id).where(User.email == settings.admin_email))
        if exists:
            logger.info("admin already exists: %s", settings.admin_email)
            return
        db.add(
            User(
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                name=settings.admin_name,
                role=ROLE_ADMIN,
            )
        )
        db.commit()
        logger.info("initial admin created: %s", settings.admin_email)


if __name__ == "__main__":
    create_initial_admin()
