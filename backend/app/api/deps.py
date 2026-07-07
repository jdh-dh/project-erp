"""API 공통 의존성 (인증, 권한)."""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, ForbiddenError
from app.core.security import TOKEN_TYPE_ACCESS, decode_token
from app.db.session import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise AuthError("인증이 필요합니다.", code="NOT_AUTHENTICATED")
    user_id = decode_token(credentials.credentials, TOKEN_TYPE_ACCESS)
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise AuthError("비활성화된 계정입니다.", code="USER_INACTIVE")
    return user


def require_roles(*roles: str):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError("권한이 없습니다.", code="INSUFFICIENT_ROLE")
        return current_user

    return checker
