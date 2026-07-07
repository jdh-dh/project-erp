"""테스트 공통 설정. 테스트 전용 PostgreSQL(erp_test)을 사용한다."""
import os

# app 모듈 import 전에 테스트 환경변수를 설정한다.
os.environ["ERP_DATABASE_URL"] = "postgresql+psycopg2://erp:erp@localhost:5432/erp_test"
os.environ["ERP_JWT_SECRET"] = "test-secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User

engine = create_engine(os.environ["ERP_DATABASE_URL"])
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture()
def db():
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def make_user(db):
    """사용자 생성 팩토리. (email, role) → User"""

    def _make(email: str, role: str = "member", password: str = "password123", active: bool = True):
        user = User(
            email=email,
            password_hash=hash_password(password),
            name=email.split("@")[0],
            role=role,
            is_active=active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make


@pytest.fixture()
def auth_headers(client, make_user):
    """역할별 사용자 생성 + 로그인하여 Authorization 헤더 반환 팩토리."""

    def _headers(role: str = "admin", email: str | None = None):
        email = email or f"{role}@test.com"
        make_user(email, role=role)
        res = client.post(
            "/api/auth/login", json={"email": email, "password": "password123"}
        )
        assert res.status_code == 200, res.text
        return {"Authorization": f"Bearer {res.json()['access_token']}"}

    return _headers
