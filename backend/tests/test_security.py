"""UT-AUTH-01, UT-AUTH-02: 비밀번호 해시 및 JWT 단위시험."""
from datetime import timedelta

import pytest

from app.core.exceptions import AuthError
from app.core.security import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    _create_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHash:
    def test_hash_and_verify(self):
        hashed = hash_password("secret123")
        assert hashed != "secret123"
        assert verify_password("secret123", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("secret123")
        assert not verify_password("wrong-password", hashed)

    def test_invalid_hash_fails(self):
        assert not verify_password("secret123", "not-a-bcrypt-hash")


class TestJwt:
    def test_access_token_roundtrip(self):
        token = create_access_token(42)
        assert decode_token(token, TOKEN_TYPE_ACCESS) == 42

    def test_refresh_token_roundtrip(self):
        token = create_refresh_token(7)
        assert decode_token(token, TOKEN_TYPE_REFRESH) == 7

    def test_expired_token_rejected(self):
        token = _create_token(1, TOKEN_TYPE_ACCESS, timedelta(seconds=-10))
        with pytest.raises(AuthError) as exc:
            decode_token(token, TOKEN_TYPE_ACCESS)
        assert exc.value.code == "TOKEN_EXPIRED"

    def test_tampered_token_rejected(self):
        token = create_access_token(1) + "x"
        with pytest.raises(AuthError) as exc:
            decode_token(token, TOKEN_TYPE_ACCESS)
        assert exc.value.code == "TOKEN_INVALID"

    def test_wrong_token_type_rejected(self):
        refresh = create_refresh_token(1)
        with pytest.raises(AuthError) as exc:
            decode_token(refresh, TOKEN_TYPE_ACCESS)
        assert exc.value.code == "TOKEN_INVALID"
