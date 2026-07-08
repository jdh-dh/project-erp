"""UT-TC-01~02, UT-ISS-01~03, UT-DOC-01~02, IT-16~18: 시험/이슈/문서 관리 시험."""
from datetime import date

import pytest

TODAY = date.today().isoformat()


@pytest.fixture()
def manager_headers(auth_headers):
    return auth_headers("manager")


@pytest.fixture()
def project(client, manager_headers, make_user):
    customer = client.post(
        "/api/customers", json={"name": "P4고객사"}, headers=manager_headers
    ).json()
    pm = make_user("p4-pm@test.com", role="manager")
    return client.post(
        "/api/projects",
        json={
            "code": "PRJ-P4",
            "name": "Phase4 프로젝트",
            "customer_id": customer["id"],
            "project_type": "HYBRID",
            "manager_id": pm.id,
        },
        headers=manager_headers,
    ).json()


class TestTestCases:
    def test_case_crud(self, client, manager_headers, project):
        """UT-TC-01: 등록, 유형 검증, 수정·논리 삭제."""
        pid = project["id"]
        res = client.post(
            f"/api/projects/{pid}/test-cases",
            json={"test_type": "UNIT", "name": "전원부 시험", "expected_result": "3.3V 출력"},
            headers=manager_headers,
        )
        assert res.status_code == 201
        case = res.json()
        assert case["last_result"] is None

        res = client.post(
            f"/api/projects/{pid}/test-cases",
            json={"test_type": "INVALID", "name": "x"},
            headers=manager_headers,
        )
        assert res.status_code == 422

        res = client.patch(
            f"/api/projects/{pid}/test-cases/{case['id']}",
            json={"name": "전원부 출력 시험"},
            headers=manager_headers,
        )
        assert res.json()["name"] == "전원부 출력 시험"

        res = client.patch(
            f"/api/projects/{pid}/test-cases/{case['id']}/deactivate",
            headers=manager_headers,
        )
        assert res.status_code == 204
        assert (
            client.get(
                f"/api/projects/{pid}/test-cases/{case['id']}", headers=manager_headers
            ).status_code
            == 404
        )

    def test_runs_and_last_result(self, client, manager_headers, project):
        """UT-TC-02 / IT-16: FAIL → PASS 기록 후 최근 결과 PASS."""
        pid = project["id"]
        case = client.post(
            f"/api/projects/{pid}/test-cases",
            json={"test_type": "INTEGRATION", "name": "통신 시험"},
            headers=manager_headers,
        ).json()
        url = f"/api/projects/{pid}/test-cases/{case['id']}/runs"

        res = client.post(
            url, json={"run_date": TODAY, "result": "FAIL", "note": "CRC 오류"},
            headers=manager_headers,
        )
        assert res.status_code == 201
        assert res.json()["tester_name"] == "manager"  # 시험자 자동 기록

        client.post(url, json={"run_date": TODAY, "result": "PASS"}, headers=manager_headers)

        detail = client.get(
            f"/api/projects/{pid}/test-cases/{case['id']}", headers=manager_headers
        ).json()
        assert detail["last_result"] == "PASS"
        assert len(detail["runs"]) == 2

        # 목록에도 최근 결과 포함
        cases = client.get(
            f"/api/projects/{pid}/test-cases?test_type=INTEGRATION",
            headers=manager_headers,
        ).json()
        assert cases[0]["last_result"] == "PASS"

    def test_member_can_record_run_but_not_create_case(self, client, auth_headers, manager_headers, project):
        pid = project["id"]
        case = client.post(
            f"/api/projects/{pid}/test-cases",
            json={"test_type": "FIELD", "name": "현장 시험"},
            headers=manager_headers,
        ).json()
        member = auth_headers("member")

        res = client.post(
            f"/api/projects/{pid}/test-cases",
            json={"test_type": "UNIT", "name": "x"},
            headers=member,
        )
        assert res.status_code == 403

        res = client.post(
            f"/api/projects/{pid}/test-cases/{case['id']}/runs",
            json={"run_date": TODAY, "result": "PASS"},
            headers=member,
        )
        assert res.status_code == 201


class TestIssues:
    def test_member_creates_issue(self, client, auth_headers, project):
        """UT-ISS-01: member 등록 가능, 등록자 자동 기록."""
        headers = auth_headers("member", email="reporter@test.com")
        res = client.post(
            f"/api/projects/{project['id']}/issues",
            json={"issue_type": "BUG", "title": "부팅 실패", "severity": "CRITICAL"},
            headers=headers,
        )
        assert res.status_code == 201
        issue = res.json()
        assert issue["status"] == "OPEN"
        assert issue["reporter_name"] == "reporter"

        res = client.post(
            f"/api/projects/{project['id']}/issues",
            json={"issue_type": "WRONG", "title": "x"},
            headers=headers,
        )
        assert res.status_code == 422

    def test_full_flow_with_history(self, client, manager_headers, project, make_user):
        """IT-17 / UT-ISS-02: OPEN→IN_PROGRESS→RESOLVED→CLOSED + 이력."""
        pid = project["id"]
        assignee = make_user("fixer@test.com")
        issue = client.post(
            f"/api/projects/{pid}/issues",
            json={"issue_type": "FAILURE", "title": "현장 장애", "assignee_id": assignee.id},
            headers=manager_headers,
        ).json()
        iid = issue["id"]
        status_url = f"/api/projects/{pid}/issues/{iid}/status"

        assert client.patch(
            status_url, json={"status": "IN_PROGRESS"}, headers=manager_headers
        ).status_code == 200

        # 원인 분석 기록
        res = client.patch(
            f"/api/projects/{pid}/issues/{iid}",
            json={"cause_analysis": "전원 커넥터 접촉 불량"},
            headers=manager_headers,
        )
        assert res.json()["cause_analysis"] == "전원 커넥터 접촉 불량"

        # RESOLVED는 조치 결과 필수 (UT-ISS-02)
        res = client.patch(status_url, json={"status": "RESOLVED"}, headers=manager_headers)
        assert res.status_code == 400
        assert res.json()["code"] == "RESOLUTION_REQUIRED"

        res = client.patch(
            status_url,
            json={"status": "RESOLVED", "resolution": "커넥터 교체 및 재조립"},
            headers=manager_headers,
        )
        assert res.status_code == 200
        assert res.json()["resolved_date"] == TODAY

        assert client.patch(
            status_url, json={"status": "CLOSED"}, headers=manager_headers
        ).status_code == 200

        # CLOSED 후 전이 불가
        res = client.patch(status_url, json={"status": "OPEN"}, headers=manager_headers)
        assert res.status_code == 400

        # 변경 이력: CREATE + UPDATE + STATUS_CHANGE x3
        logs = client.get(
            f"/api/change-logs?entity_type=issue&entity_id={iid}",
            headers=manager_headers,
        ).json()["items"]
        actions = [log["action"] for log in logs]
        assert actions.count("STATUS_CHANGE") == 3
        assert actions[-1] == "CREATE"

    def test_assignee_permission(self, client, auth_headers, manager_headers, project):
        """UT-ISS-03: 담당자 수정 가능, 무관 member 403."""
        pid = project["id"]
        assignee_headers = auth_headers("member", email="issue-assignee@test.com")
        me = client.get("/api/auth/me", headers=assignee_headers).json()

        issue = client.post(
            f"/api/projects/{pid}/issues",
            json={"issue_type": "BUG", "title": "담당 이슈", "assignee_id": me["id"]},
            headers=manager_headers,
        ).json()

        # 담당자 수정 성공
        res = client.patch(
            f"/api/projects/{pid}/issues/{issue['id']}",
            json={"cause_analysis": "분석 완료"},
            headers=assignee_headers,
        )
        assert res.status_code == 200

        # 무관한 member 수정 403
        other = auth_headers("member", email="other-member@test.com")
        res = client.patch(
            f"/api/projects/{pid}/issues/{issue['id']}",
            json={"title": "변조"},
            headers=other,
        )
        assert res.status_code == 403
        assert res.json()["code"] == "NOT_ISSUE_EDITOR"

    def test_list_filters(self, client, manager_headers, project):
        pid = project["id"]
        for issue_type, title in (("BUG", "버그1"), ("IMPROVEMENT", "개선1")):
            client.post(
                f"/api/projects/{pid}/issues",
                json={"issue_type": issue_type, "title": title},
                headers=manager_headers,
            )
        res = client.get(
            f"/api/projects/{pid}/issues?issue_type=BUG", headers=manager_headers
        )
        assert [i["title"] for i in res.json()] == ["버그1"]
        res = client.get(
            f"/api/projects/{pid}/issues?status=OPEN", headers=manager_headers
        )
        assert len(res.json()) == 2


class TestDocuments:
    def test_document_flow(self, client, manager_headers, project):
        """UT-DOC-01 / IT-18: 등록(작성자 자동) → 버전 갱신 → 이력."""
        pid = project["id"]
        res = client.post(
            f"/api/projects/{pid}/documents",
            json={
                "doc_type": "DESIGN",
                "title": "제어보드 설계서",
                "version": "1.0",
                "file_url": "https://drive.example.com/design-v1",
            },
            headers=manager_headers,
        )
        assert res.status_code == 201
        doc = res.json()
        assert doc["author_name"] == "manager"

        res = client.patch(
            f"/api/projects/{pid}/documents/{doc['id']}",
            json={"version": "1.1", "file_url": "https://drive.example.com/design-v1.1"},
            headers=manager_headers,
        )
        assert res.json()["version"] == "1.1"

        docs = client.get(
            f"/api/projects/{pid}/documents?doc_type=DESIGN", headers=manager_headers
        ).json()
        assert len(docs) == 1

        logs = client.get(
            f"/api/change-logs?entity_type=document&entity_id={doc['id']}",
            headers=manager_headers,
        ).json()["items"]
        assert [log["action"] for log in logs] == ["UPDATE", "CREATE"]

        res = client.post(
            f"/api/projects/{pid}/documents",
            json={"doc_type": "NOPE", "title": "x"},
            headers=manager_headers,
        )
        assert res.status_code == 422

    def test_member_cannot_create(self, client, auth_headers, project):
        """UT-DOC-02: member 문서 등록 403."""
        headers = auth_headers("member")
        res = client.post(
            f"/api/projects/{project['id']}/documents",
            json={"doc_type": "OTHER", "title": "무단 문서"},
            headers=headers,
        )
        assert res.status_code == 403
