"""인증 서비스."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError
from app.core.logging import get_logger
from app.core.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models import User

logger = get_logger(__name__)


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.password_hash):
        logger.warning("login failed: email=%s", email)
        raise AuthError("이메일 또는 비밀번호가 올바르지 않습니다.", code="LOGIN_FAILED")
    if not user.is_active:
        logger.warning("login blocked (inactive): email=%s", email)
        raise AuthError("비활성화된 계정입니다.", code="USER_INACTIVE")
    return user


def issue_tokens(user: User) -> dict:
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
    }


def refresh_tokens(db: Session, refresh_token: str) -> dict:
    user_id = decode_token(refresh_token, TOKEN_TYPE_REFRESH)
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise AuthError("비활성화된 계정입니다.", code="USER_INACTIVE")
    return issue_tokens(user)
