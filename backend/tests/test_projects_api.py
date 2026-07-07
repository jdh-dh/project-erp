"""UT-PROJ-01, UT-PROJ-02, UT-COM-01, IT-05, IT-06, IT-07: 프로젝트 관리 시험."""
import pytest


@pytest.fixture()
def manager_headers(auth_headers):
    return auth_headers("manager")


@pytest.fixture()
def setup_refs(client, manager_headers, make_user):
    """프로젝트 생성에 필요한 고객사·PM 준비."""
    res = client.post(
        "/api/customers", json={"name": "고객사A"}, headers=manager_headers
    )
    customer_id = res.json()["id"]
    pm = make_user("pm@test.com", role="manager")
    return {"customer_id": customer_id, "manager_id": pm.id}


def _create_project(client, headers, refs, code="PRJ-001", **overrides):
    payload = {
        "code": code,
        "name": "테스트 프로젝트",
        "customer_id": refs["customer_id"],
        "project_type": "HYBRID",
        "manager_id": refs["manager_id"],
        "start_date": "2026-07-01",
        "end_date": "2026-12-31",
        "description": "설명",
    }
    payload.update(overrides)
    return client.post("/api/projects", json=payload, headers=headers)


class TestProjectCrud:
    def test_create_and_detail(self, client, manager_headers, setup_refs):
        """IT-05: 프로젝트 등록 → 상세 조회 → 참여자 설정 → 계약 등록."""
        res = _create_project(client, manager_headers, setup_refs)
        assert res.status_code == 201, res.text
        project = res.json()
        assert project["code"] == "PRJ-001"
        assert project["status"] == "PLANNED"
        assert project["customer_name"] == "고객사A"
        assert project["manager_name"] == "pm"

        # 참여자 설정
        res = client.put(
            f"/api/projects/{project['id']}/members",
            json={"members": [{"user_id": setup_refs["manager_id"], "role": "HW개발"}]},
            headers=manager_headers,
        )
        assert res.status_code == 200
        assert res.json()["members"][0]["role"] == "HW개발"

        # 계약 등록
        res = client.post(
            f"/api/projects/{project['id']}/contracts",
            json={"contract_no": "CT-2026-01", "amount": "50000000"},
            headers=manager_headers,
        )
        assert res.status_code == 201
        assert res.json()["status"] == "ACTIVE"

        # 상세 조회에 참여자·계약 포함
        res = client.get(f"/api/projects/{project['id']}", headers=manager_headers)
        detail = res.json()
        assert len(detail["members"]) == 1
        assert len(detail["contracts"]) == 1

    def test_duplicate_code(self, client, manager_headers, setup_refs):
        """IT-07 / UT-PROJ-01: 중복 프로젝트 코드 → 409."""
        assert _create_project(client, manager_headers, setup_refs).status_code == 201
        res = _create_project(client, manager_headers, setup_refs)
        assert res.status_code == 409
        assert res.json()["code"] == "PROJECT_CODE_DUPLICATED"

    def test_unknown_customer(self, client, manager_headers, setup_refs):
        res = _create_project(
            client, manager_headers, setup_refs, code="PRJ-X", customer_id=99999
        )
        assert res.status_code == 404

    def test_member_cannot_create(self, client, auth_headers, setup_refs, manager_headers):
        headers = auth_headers("member")
        res = _create_project(client, headers, setup_refs, code="PRJ-M")
        assert res.status_code == 403

    def test_list_filter(self, client, manager_headers, setup_refs):
        _create_project(client, manager_headers, setup_refs, code="PRJ-A")
        _create_project(client, manager_headers, setup_refs, code="PRJ-B")
        res = client.get("/api/projects?q=PRJ-A", headers=manager_headers)
        assert res.json()["total"] == 1
        res = client.get("/api/projects?status=PLANNED", headers=manager_headers)
        assert res.json()["total"] == 2


class TestStatusTransition:
    def test_full_flow_with_history(self, client, manager_headers, setup_refs):
        """IT-06 / UT-PROJ-02: PLANNED→IN_PROGRESS→COMPLETED 및 이력 조회."""
        project = _create_project(client, manager_headers, setup_refs).json()
        pid = project["id"]

        res = client.patch(
            f"/api/projects/{pid}/status",
            json={"status": "IN_PROGRESS"},
            headers=manager_headers,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "IN_PROGRESS"

        res = client.patch(
            f"/api/projects/{pid}/status",
            json={"status": "COMPLETED"},
            headers=manager_headers,
        )
        assert res.status_code == 200

        # 변경 이력: CREATE + STATUS_CHANGE x2 (UT-COM-01)
        res = client.get(
            f"/api/change-logs?entity_type=project&entity_id={pid}",
            headers=manager_headers,
        )
        actions = [log["action"] for log in res.json()["items"]]
        assert actions == ["STATUS_CHANGE", "STATUS_CHANGE", "CREATE"]

    def test_invalid_transition(self, client, manager_headers, setup_refs):
        """UT-PROJ-02: 비허용 전이(COMPLETED→IN_PROGRESS) 거부."""
        project = _create_project(client, manager_headers, setup_refs).json()
        pid = project["id"]
        for status in ("IN_PROGRESS", "COMPLETED"):
            client.patch(
                f"/api/projects/{pid}/status",
                json={"status": status},
                headers=manager_headers,
            )
        res = client.patch(
            f"/api/projects/{pid}/status",
            json={"status": "IN_PROGRESS"},
            headers=manager_headers,
        )
        assert res.status_code == 400
        assert res.json()["code"] == "INVALID_STATUS_TRANSITION"

    def test_planned_to_completed_rejected(self, client, manager_headers, setup_refs):
        project = _create_project(client, manager_headers, setup_refs).json()
        res = client.patch(
            f"/api/projects/{project['id']}/status",
            json={"status": "COMPLETED"},
            headers=manager_headers,
        )
        assert res.status_code == 400


class TestContract:
    def test_update_contract(self, client, manager_headers, setup_refs):
        project = _create_project(client, manager_headers, setup_refs).json()
        contract = client.post(
            f"/api/projects/{project['id']}/contracts",
            json={"contract_no": "CT-01"},
            headers=manager_headers,
        ).json()
        res = client.patch(
            f"/api/projects/{project['id']}/contracts/{contract['id']}",
            json={"status": "CLOSED"},
            headers=manager_headers,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "CLOSED"
