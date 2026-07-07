"""IT-01, IT-02, IT-08: 인증 API 통합시험."""


class TestLoginFlow:
    def test_login_me_refresh(self, client, make_user):
        """IT-01: 로그인 → 토큰 발급 → me 조회 → 토큰 재발급."""
        make_user("user1@test.com", role="member")

        res = client.post(
            "/api/auth/login",
            json={"email": "user1@test.com", "password": "password123"},
        )
        assert res.status_code == 200
        tokens = res.json()
        assert tokens["access_token"] and tokens["refresh_token"]

        res = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert res.status_code == 200
        assert res.json()["email"] == "user1@test.com"

        res = client.post(
            "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        assert res.status_code == 200
        assert res.json()["access_token"]

    def test_wrong_password(self, client, make_user):
        """IT-02: 잘못된 비밀번호 → 401."""
        make_user("user2@test.com")
        res = client.post(
            "/api/auth/login",
            json={"email": "user2@test.com", "password": "bad-password"},
        )
        assert res.status_code == 401
        assert res.json()["code"] == "LOGIN_FAILED"

    def test_inactive_user_login(self, client, make_user):
        """IT-02: 비활성 사용자 로그인 → 401."""
        make_user("inactive@test.com", active=False)
        res = client.post(
            "/api/auth/login",
            json={"email": "inactive@test.com", "password": "password123"},
        )
        assert res.status_code == 401
        assert res.json()["code"] == "USER_INACTIVE"

    def test_unknown_email(self, client):
        res = client.post(
            "/api/auth/login",
            json={"email": "nobody@test.com", "password": "password123"},
        )
        assert res.status_code == 401


class TestProtectedApi:
    def test_no_token(self, client):
        """IT-08: 인증 없이 보호 API 호출 → 401."""
        assert client.get("/api/projects").status_code == 401

    def test_invalid_token(self, client):
        res = client.get(
            "/api/projects", headers={"Authorization": "Bearer invalid-token"}
        )
        assert res.status_code == 401
