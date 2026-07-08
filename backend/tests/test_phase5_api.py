"""UT-REL-01, UT-COST-01~02, UT-RPT-01, IT-19~20: 릴리즈/비용/보고서 시험."""
from datetime import date

import pytest

TODAY = date.today().isoformat()


@pytest.fixture()
def manager_headers(auth_headers):
    return auth_headers("manager")


@pytest.fixture()
def project(client, manager_headers, make_user):
    customer = client.post(
        "/api/customers", json={"name": "P5고객사"}, headers=manager_headers
    ).json()
    pm = make_user("p5-pm@test.com", role="manager")
    return client.post(
        "/api/projects",
        json={
            "code": "PRJ-P5",
            "name": "Phase5 프로젝트",
            "customer_id": customer["id"],
            "project_type": "HYBRID",
            "manager_id": pm.id,
        },
        headers=manager_headers,
    ).json()


class TestReleases:
    def test_release_crud(self, client, manager_headers, project):
        """UT-REL-01: 등록(등록자 자동), 버전 중복 409, 수정·삭제·이력."""
        pid = project["id"]
        url = f"/api/projects/{pid}/releases"
        res = client.post(
            url,
            json={
                "version": "1.0.0",
                "title": "최초 출시",
                "release_date": TODAY,
                "content": "최초 기능 릴리즈",
            },
            headers=manager_headers,
        )
        assert res.status_code == 201
        release = res.json()
        assert release["creator_name"] == "manager"

        # 버전 중복 409
        res = client.post(
            url,
            json={"version": "1.0.0", "title": "중복", "release_date": TODAY},
            headers=manager_headers,
        )
        assert res.status_code == 409
        assert res.json()["code"] == "RELEASE_DUPLICATED"

        # 수정
        res = client.patch(
            f"{url}/{release['id']}",
            json={"title": "최초 정식 출시"},
            headers=manager_headers,
        )
        assert res.json()["title"] == "최초 정식 출시"

        # 이력
        logs = client.get(
            f"/api/change-logs?entity_type=release&entity_id={release['id']}",
            headers=manager_headers,
        ).json()["items"]
        assert [log["action"] for log in logs] == ["UPDATE", "CREATE"]

        # 논리 삭제 후 같은 버전 재등록 가능
        client.patch(f"{url}/{release['id']}/deactivate", headers=manager_headers)
        res = client.post(
            url,
            json={"version": "1.0.0", "title": "재등록", "release_date": TODAY},
            headers=manager_headers,
        )
        assert res.status_code == 201

    def test_member_cannot_create(self, client, auth_headers, project):
        """IT-20: member 릴리즈 등록 403."""
        headers = auth_headers("member")
        res = client.post(
            f"/api/projects/{project['id']}/releases",
            json={"version": "9.9", "title": "x", "release_date": TODAY},
            headers=headers,
        )
        assert res.status_code == 403


class TestCosts:
    def test_cost_validation(self, client, manager_headers, project):
        """UT-COST-01: 등록, 분류 검증, 금액 0 이하 거부."""
        pid = project["id"]
        url = f"/api/projects/{pid}/costs"
        res = client.post(
            url,
            json={"cost_date": TODAY, "category": "MATERIAL", "item": "MCU 구매", "amount": "1500000"},
            headers=manager_headers,
        )
        assert res.status_code == 201
        assert res.json()["creator_name"] == "manager"

        res = client.post(
            url,
            json={"cost_date": TODAY, "category": "WRONG", "item": "x", "amount": "100"},
            headers=manager_headers,
        )
        assert res.status_code == 422

        res = client.post(
            url,
            json={"cost_date": TODAY, "category": "ETC", "item": "x", "amount": "0"},
            headers=manager_headers,
        )
        assert res.status_code == 422

    def test_cost_summary_excludes_inactive(self, client, manager_headers, project):
        """UT-COST-02: 총액·분류별 합계, 비활성 제외."""
        pid = project["id"]
        url = f"/api/projects/{pid}/costs"
        client.post(
            url,
            json={"cost_date": TODAY, "category": "LABOR", "item": "개발 인건비", "amount": "8000000"},
            headers=manager_headers,
        )
        client.post(
            url,
            json={"cost_date": TODAY, "category": "MATERIAL", "item": "부품비", "amount": "4500000"},
            headers=manager_headers,
        )
        excluded = client.post(
            url,
            json={"cost_date": TODAY, "category": "ETC", "item": "취소 비용", "amount": "999999"},
            headers=manager_headers,
        ).json()
        client.patch(f"{url}/{excluded['id']}/deactivate", headers=manager_headers)

        summary = client.get(f"{url}/summary", headers=manager_headers).json()
        assert summary["total"] == "12500000"
        assert summary["by_category"] == {"LABOR": "8000000", "MATERIAL": "4500000"}

    def test_member_cannot_create(self, client, auth_headers, project):
        """IT-20: member 비용 등록 403."""
        headers = auth_headers("member")
        res = client.post(
            f"/api/projects/{project['id']}/costs",
            json={"cost_date": TODAY, "category": "ETC", "item": "x", "amount": "100"},
            headers=headers,
        )
        assert res.status_code == 403


class TestReport:
    def test_full_report(self, client, manager_headers, project):
        """UT-RPT-01 / IT-19: 전 영역 데이터 등록 후 보고서 집계 검증."""
        pid = project["id"]

        # 일정: WBS 2건 (progress 100, 50)
        client.post(
            f"/api/projects/{pid}/wbs", json={"name": "w1", "progress": 100},
            headers=manager_headers,
        )
        client.post(
            f"/api/projects/{pid}/wbs", json={"name": "w2", "progress": 50},
            headers=manager_headers,
        )
        # 이슈: OPEN 1건, RESOLVED 1건
        client.post(
            f"/api/projects/{pid}/issues",
            json={"issue_type": "BUG", "title": "이슈1"},
            headers=manager_headers,
        )
        issue2 = client.post(
            f"/api/projects/{pid}/issues",
            json={"issue_type": "FAILURE", "title": "이슈2"},
            headers=manager_headers,
        ).json()
        client.patch(
            f"/api/projects/{pid}/issues/{issue2['id']}/status",
            json={"status": "RESOLVED", "resolution": "조치"},
            headers=manager_headers,
        )
        # 시험: PASS 1건, 미실행 1건
        case1 = client.post(
            f"/api/projects/{pid}/test-cases",
            json={"test_type": "UNIT", "name": "tc1"},
            headers=manager_headers,
        ).json()
        client.post(
            f"/api/projects/{pid}/test-cases/{case1['id']}/runs",
            json={"run_date": TODAY, "result": "PASS"},
            headers=manager_headers,
        )
        client.post(
            f"/api/projects/{pid}/test-cases",
            json={"test_type": "FIELD", "name": "tc2"},
            headers=manager_headers,
        )
        # HW 보드 1건
        client.post(
            f"/api/projects/{pid}/hw/boards",
            json={"name": "보드", "revision": "A0"},
            headers=manager_headers,
        )
        # SW 모듈 1건 + 버전 2건(1건 릴리즈)
        module = client.post(
            f"/api/projects/{pid}/sw/modules",
            json={"name": "모듈", "module_type": "FIRMWARE"},
            headers=manager_headers,
        ).json()
        v1 = client.post(
            f"/api/projects/{pid}/sw/modules/{module['id']}/versions",
            json={"version": "1.0"},
            headers=manager_headers,
        ).json()
        client.post(
            f"/api/projects/{pid}/sw/modules/{module['id']}/versions",
            json={"version": "1.1"},
            headers=manager_headers,
        )
        client.patch(
            f"/api/projects/{pid}/sw/modules/{module['id']}/versions/{v1['id']}/release",
            headers=manager_headers,
        )
        # 릴리즈 1건, 비용 1건
        client.post(
            f"/api/projects/{pid}/releases",
            json={"version": "1.0", "title": "출시", "release_date": TODAY},
            headers=manager_headers,
        )
        client.post(
            f"/api/projects/{pid}/costs",
            json={"cost_date": TODAY, "category": "LABOR", "item": "인건비", "amount": "1000000"},
            headers=manager_headers,
        )

        report = client.get(f"/api/projects/{pid}/report", headers=manager_headers).json()
        assert report["project"]["code"] == "PRJ-P5"
        assert report["schedule"]["progress"] == 75.0
        assert report["schedule"]["wbs_total"] == 2
        assert report["issues"] == {
            "total": 2, "open": 1, "in_progress": 0, "resolved": 1, "closed": 0,
        }
        assert report["tests"] == {
            "total": 2, "passed": 1, "failed": 0, "blocked": 0, "not_run": 1,
        }
        assert report["hardware"] == {"boards": 1}
        assert report["software"] == {
            "modules": 1, "versions": 2, "released_versions": 1,
        }
        assert report["releases"] == 1
        assert report["costs"]["total"] == "1000000"

    def test_empty_project_report(self, client, manager_headers, project):
        report = client.get(
            f"/api/projects/{project['id']}/report", headers=manager_headers
        ).json()
        assert report["issues"]["total"] == 0
        assert report["tests"]["total"] == 0
        assert report["costs"]["total"] == "0"
