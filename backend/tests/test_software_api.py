"""UT-SW-01~04, IT-14, IT-15: 소프트웨어 관리 시험."""
from datetime import date

import pytest


@pytest.fixture()
def manager_headers(auth_headers):
    return auth_headers("manager")


@pytest.fixture()
def project(client, manager_headers, make_user):
    customer = client.post(
        "/api/customers", json={"name": "SW고객사"}, headers=manager_headers
    ).json()
    pm = make_user("sw-pm@test.com", role="manager")
    return client.post(
        "/api/projects",
        json={
            "code": "PRJ-SW",
            "name": "SW 프로젝트",
            "customer_id": customer["id"],
            "project_type": "SW",
            "manager_id": pm.id,
        },
        headers=manager_headers,
    ).json()


def _create_module(client, headers, project_id, name="펌웨어", **overrides):
    payload = {"name": name, "module_type": "FIRMWARE"}
    payload.update(overrides)
    return client.post(
        f"/api/projects/{project_id}/sw/modules", json=payload, headers=headers
    )


class TestModule:
    def test_create_and_duplicate(self, client, manager_headers, project):
        """UT-SW-01: 등록, 이름 중복 409, 유형 검증."""
        pid = project["id"]
        res = _create_module(
            client, manager_headers, pid,
            repo_url="https://github.com/jdh-dh/firmware",
        )
        assert res.status_code == 201
        assert res.json()["repo_url"] == "https://github.com/jdh-dh/firmware"

        res = _create_module(client, manager_headers, pid)
        assert res.status_code == 409
        assert res.json()["code"] == "MODULE_DUPLICATED"

        res = _create_module(client, manager_headers, pid, name="X", module_type="INVALID")
        assert res.status_code == 422

    def test_member_cannot_create(self, client, auth_headers, project):
        """IT-15: member 모듈 등록 → 403."""
        headers = auth_headers("member")
        res = _create_module(client, headers, project["id"])
        assert res.status_code == 403


class TestVersion:
    def test_version_duplicate(self, client, manager_headers, project):
        """UT-SW-02: 모듈 내 버전 중복 409."""
        pid = project["id"]
        module = _create_module(client, manager_headers, pid).json()
        url = f"/api/projects/{pid}/sw/modules/{module['id']}/versions"

        assert client.post(url, json={"version": "1.0.0"}, headers=manager_headers).status_code == 201
        res = client.post(url, json={"version": "1.0.0"}, headers=manager_headers)
        assert res.status_code == 409
        assert res.json()["code"] == "VERSION_DUPLICATED"

    def test_release(self, client, manager_headers, project):
        """UT-SW-03: 릴리즈 처리, 중복 릴리즈 400."""
        pid = project["id"]
        module = _create_module(client, manager_headers, pid, name="앱").json()
        version = client.post(
            f"/api/projects/{pid}/sw/modules/{module['id']}/versions",
            json={"version": "2.0.0"},
            headers=manager_headers,
        ).json()
        url = f"/api/projects/{pid}/sw/modules/{module['id']}/versions/{version['id']}/release"

        res = client.patch(url, headers=manager_headers)
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "RELEASED"
        assert body["released_date"] == date.today().isoformat()

        res = client.patch(url, headers=manager_headers)
        assert res.status_code == 400
        assert res.json()["code"] == "ALREADY_RELEASED"

    def test_full_flow(self, client, manager_headers, project):
        """IT-14 / UT-SW-04: 모듈 → 버전 → 빌드 → 배포 → 릴리즈 → 상세."""
        pid = project["id"]
        module = _create_module(client, manager_headers, pid, name="서버").json()
        mid = module["id"]
        version = client.post(
            f"/api/projects/{pid}/sw/modules/{mid}/versions",
            json={"version": "0.1.0", "note": "최초 버전"},
            headers=manager_headers,
        ).json()
        vid = version["id"]
        base = f"/api/projects/{pid}/sw/modules/{mid}/versions/{vid}"

        res = client.post(
            f"{base}/builds",
            json={"build_no": "42", "commit_hash": "abc1234", "result": "SUCCESS"},
            headers=manager_headers,
        )
        assert res.status_code == 201
        assert res.json()["commit_hash"] == "abc1234"

        res = client.post(
            f"{base}/deployments",
            json={"environment": "DEV", "note": "개발 서버 배포"},
            headers=manager_headers,
        )
        assert res.status_code == 201

        client.patch(f"{base}/release", headers=manager_headers)

        detail = client.get(base, headers=manager_headers).json()
        assert detail["status"] == "RELEASED"
        assert len(detail["builds"]) == 1
        assert len(detail["deployments"]) == 1

        # 모듈 상세에 버전 포함
        module_detail = client.get(
            f"/api/projects/{pid}/sw/modules/{mid}", headers=manager_headers
        ).json()
        assert [v["version"] for v in module_detail["versions"]] == ["0.1.0"]

    def test_deactivate_module_hides_versions(self, client, manager_headers, project):
        """UT-SW-01/REQ-SW-009: 모듈 논리 삭제 시 버전 접근 불가."""
        pid = project["id"]
        module = _create_module(client, manager_headers, pid, name="삭제모듈").json()
        client.post(
            f"/api/projects/{pid}/sw/modules/{module['id']}/versions",
            json={"version": "1.0.0"},
            headers=manager_headers,
        )
        res = client.patch(
            f"/api/projects/{pid}/sw/modules/{module['id']}/deactivate",
            headers=manager_headers,
        )
        assert res.status_code == 204
        res = client.get(
            f"/api/projects/{pid}/sw/modules/{module['id']}", headers=manager_headers
        )
        assert res.status_code == 404
