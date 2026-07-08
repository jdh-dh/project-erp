"""UT-HW-01~04, IT-13, IT-15: 하드웨어 관리 시험."""
import pytest


@pytest.fixture()
def manager_headers(auth_headers):
    return auth_headers("manager")


@pytest.fixture()
def project(client, manager_headers, make_user):
    customer = client.post(
        "/api/customers", json={"name": "HW고객사"}, headers=manager_headers
    ).json()
    pm = make_user("hw-pm@test.com", role="manager")
    return client.post(
        "/api/projects",
        json={
            "code": "PRJ-HW",
            "name": "HW 프로젝트",
            "customer_id": customer["id"],
            "project_type": "HW",
            "manager_id": pm.id,
        },
        headers=manager_headers,
    ).json()


def _create_board(client, headers, project_id, name="메인보드", revision="A0", **overrides):
    payload = {"name": name, "revision": revision}
    payload.update(overrides)
    return client.post(
        f"/api/projects/{project_id}/hw/boards", json=payload, headers=headers
    )


class TestBoard:
    def test_create_and_duplicate(self, client, manager_headers, project):
        """UT-HW-01: 등록, (이름, 리비전) 중복 409."""
        pid = project["id"]
        res = _create_board(client, manager_headers, pid)
        assert res.status_code == 201
        assert res.json()["status"] == "DESIGN"

        res = _create_board(client, manager_headers, pid)
        assert res.status_code == 409
        assert res.json()["code"] == "BOARD_DUPLICATED"

        # 다른 리비전은 허용 (REQ-HW-003)
        res = _create_board(client, manager_headers, pid, revision="B0")
        assert res.status_code == 201

    def test_status_change(self, client, manager_headers, project):
        pid = project["id"]
        board = _create_board(client, manager_headers, pid).json()
        res = client.patch(
            f"/api/projects/{pid}/hw/boards/{board['id']}",
            json={"status": "PROTOTYPE"},
            headers=manager_headers,
        )
        assert res.status_code == 200
        assert res.json()["status"] == "PROTOTYPE"

    def test_full_flow_with_history(self, client, manager_headers, project):
        """IT-13: 보드 → BOM 2건 → 상세 → 제작 이력 → 변경 이력."""
        pid = project["id"]
        board = _create_board(client, manager_headers, pid, name="제어보드").json()
        bid = board["id"]

        for part in (
            {"part_name": "MCU", "part_number": "STM32F407", "manufacturer": "ST", "quantity": 1, "reference": "U1"},
            {"part_name": "저항 10K", "quantity": 8, "reference": "R1-R8"},
        ):
            res = client.post(
                f"/api/projects/{pid}/hw/boards/{bid}/bom",
                json=part,
                headers=manager_headers,
            )
            assert res.status_code == 201

        res = client.post(
            f"/api/projects/{pid}/hw/boards/{bid}/fabrications",
            json={"fab_date": "2026-07-01", "quantity": 5, "vendor": "PCB하우스", "result": "OK"},
            headers=manager_headers,
        )
        assert res.status_code == 201

        detail = client.get(
            f"/api/projects/{pid}/hw/boards/{bid}", headers=manager_headers
        ).json()
        assert len(detail["bom_items"]) == 2
        assert len(detail["fabrications"]) == 1
        assert detail["fabrications"][0]["vendor"] == "PCB하우스"

        res = client.get(
            f"/api/change-logs?entity_type=hw_board&entity_id={bid}",
            headers=manager_headers,
        )
        assert [log["action"] for log in res.json()["items"]] == ["CREATE"]

    def test_bom_update_and_validation(self, client, manager_headers, project):
        """UT-HW-02: BOM 수정, 수량 1 미만 거부."""
        pid = project["id"]
        board = _create_board(client, manager_headers, pid, name="BOM보드").json()
        item = client.post(
            f"/api/projects/{pid}/hw/boards/{board['id']}/bom",
            json={"part_name": "커패시터", "quantity": 2},
            headers=manager_headers,
        ).json()

        res = client.patch(
            f"/api/projects/{pid}/hw/boards/{board['id']}/bom/{item['id']}",
            json={"quantity": 10},
            headers=manager_headers,
        )
        assert res.status_code == 200
        assert res.json()["quantity"] == 10

        res = client.post(
            f"/api/projects/{pid}/hw/boards/{board['id']}/bom",
            json={"part_name": "불량부품", "quantity": 0},
            headers=manager_headers,
        )
        assert res.status_code == 422

    def test_deactivate_cascades_bom(self, client, manager_headers, project):
        """UT-HW-03: 보드 비활성화 시 BOM 연쇄."""
        pid = project["id"]
        board = _create_board(client, manager_headers, pid, name="삭제보드").json()
        client.post(
            f"/api/projects/{pid}/hw/boards/{board['id']}/bom",
            json={"part_name": "부품"},
            headers=manager_headers,
        )
        res = client.patch(
            f"/api/projects/{pid}/hw/boards/{board['id']}/deactivate",
            headers=manager_headers,
        )
        assert res.status_code == 204

        res = client.get(
            f"/api/projects/{pid}/hw/boards/{board['id']}", headers=manager_headers
        )
        assert res.status_code == 404

        boards = client.get(
            f"/api/projects/{pid}/hw/boards", headers=manager_headers
        ).json()
        assert board["id"] not in [b["id"] for b in boards]

    def test_member_cannot_create(self, client, auth_headers, project):
        """IT-15: member 보드 등록 → 403."""
        headers = auth_headers("member")
        res = _create_board(client, headers, project["id"])
        assert res.status_code == 403
