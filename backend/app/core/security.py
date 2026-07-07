"""비밀번호 해시 및 JWT 토큰 처리."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import AuthError

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def _create_token(user_id: int, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _create_token(
        user_id, TOKEN_TYPE_ACCESS, timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        user_id, TOKEN_TYPE_REFRESH, timedelta(days=settings.refresh_token_expire_days)
    )


def decode_token(token: str, expected_type: str) -> int:
    """토큰을 검증하고 사용자 id를 반환한다. 실패 시 AuthError."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise AuthError("토큰이 만료되었습니다.", code="TOKEN_EXPIRED")
    except jwt.InvalidTokenError:
        raise AuthError("유효하지 않은 토큰입니다.", code="TOKEN_INVALID")

    if payload.get("type") != expected_type:
        raise AuthError("토큰 유형이 올바르지 않습니다.", code="TOKEN_INVALID")
    try:
        return int(payload["sub"])
    except (KeyError, ValueError):
        raise AuthError("유효하지 않은 토큰입니다.", code="TOKEN_INVALID")
