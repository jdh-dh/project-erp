"""UT-USER-01, IT-03: 사용자 관리 시험."""


class TestUserCrud:
    def test_admin_creates_user(self, client, auth_headers):
        headers = auth_headers("admin")
        res = client.post(
            "/api/users",
            json={
                "email": "new@test.com",
                "password": "password123",
                "name": "신규 사용자",
                "role": "member",
            },
            headers=headers,
        )
        assert res.status_code == 201
        body = res.json()
        assert body["email"] == "new@test.com"
        assert "password" not in body and "password_hash" not in body

    def test_duplicate_email_conflict(self, client, auth_headers):
        headers = auth_headers("admin")
        payload = {
            "email": "dup@test.com",
            "password": "password123",
            "name": "중복",
            "role": "member",
        }
        assert client.post("/api/users", json=payload, headers=headers).status_code == 201
        res = client.post("/api/users", json=payload, headers=headers)
        assert res.status_code == 409
        assert res.json()["code"] == "EMAIL_DUPLICATED"

    def test_member_cannot_create_user(self, client, auth_headers):
        """IT-03: member 권한으로 사용자 등록 → 403."""
        headers = auth_headers("member")
        res = client.post(
            "/api/users",
            json={
                "email": "x@test.com",
                "password": "password123",
                "name": "x",
                "role": "member",
            },
            headers=headers,
        )
        assert res.status_code == 403

    def test_deactivate_user(self, client, auth_headers, make_user):
        headers = auth_headers("admin")
        target = make_user("target@test.com")
        res = client.patch(f"/api/users/{target.id}/deactivate", headers=headers)
        assert res.status_code == 200
        assert res.json()["is_active"] is False

    def test_update_user_role(self, client, auth_headers, make_user):
        headers = auth_headers("admin")
        target = make_user("promote@test.com", role="member")
        res = client.patch(
            f"/api/users/{target.id}", json={"role": "manager"}, headers=headers
        )
        assert res.status_code == 200
        assert res.json()["role"] == "manager"

    def test_user_change_log_recorded(self, client, auth_headers):
        """UT-COM-01: 사용자 생성 시 변경 이력 기록."""
        headers = auth_headers("admin")
        res = client.post(
            "/api/users",
            json={
                "email": "logged@test.com",
                "password": "password123",
                "name": "이력",
                "role": "member",
            },
            headers=headers,
        )
        user_id = res.json()["id"]
        res = client.get(
            f"/api/change-logs?entity_type=user&entity_id={user_id}", headers=headers
        )
        assert res.status_code == 200
        logs = res.json()["items"]
        assert len(logs) == 1
        assert logs[0]["action"] == "CREATE"
        # 비밀번호 해시는 이력에 남기지 않는다
        assert "password_hash" not in logs[0]["after_data"]
