"""UT-WBS-01~05, UT-MS-01, UT-SCH-01, IT-09~12: 일정 관리 시험."""
from datetime import date, timedelta

import pytest

TODAY = date.today()
YESTERDAY = (TODAY - timedelta(days=1)).isoformat()
TOMORROW = (TODAY + timedelta(days=1)).isoformat()


@pytest.fixture()
def manager_headers(auth_headers):
    return auth_headers("manager")


@pytest.fixture()
def project(client, manager_headers, make_user):
    """WBS 시험용 프로젝트."""
    customer = client.post(
        "/api/customers", json={"name": "일정고객사"}, headers=manager_headers
    ).json()
    pm = make_user("schedule-pm@test.com", role="manager")
    res = client.post(
        "/api/projects",
        json={
            "code": "PRJ-SCH",
            "name": "일정 프로젝트",
            "customer_id": customer["id"],
            "project_type": "SW",
            "manager_id": pm.id,
        },
        headers=manager_headers,
    )
    assert res.status_code == 201, res.text
    return res.json()


def _create_wbs(client, headers, project_id, name="작업", **overrides):
    payload = {"name": name}
    payload.update(overrides)
    return client.post(f"/api/projects/{project_id}/wbs", json=payload, headers=headers)


class TestWbsCrud:
    def test_hierarchy_and_history(self, client, manager_headers, project):
        """IT-09 / UT-WBS-01: 계층 등록 → 목록 → 기간 변경 → 이력 확인."""
        pid = project["id"]
        parent = _create_wbs(client, manager_headers, pid, name="설계").json()
        child = _create_wbs(
            client, manager_headers, pid, name="상세설계", parent_id=parent["id"]
        ).json()
        assert child["parent_id"] == parent["id"]

        res = client.get(f"/api/projects/{pid}/wbs", headers=manager_headers)
        items = res.json()
        assert [(i["name"], i["depth"]) for i in items] == [("설계", 0), ("상세설계", 1)]

        # 기간 변경 (REQ-WBS-005)
        res = client.patch(
            f"/api/projects/{pid}/wbs/{child['id']}",
            json={"start_date": "2026-08-01", "end_date": "2026-08-31"},
            headers=manager_headers,
        )
        assert res.status_code == 200

        res = client.get(
            f"/api/change-logs?entity_type=wbs&entity_id={child['id']}",
            headers=manager_headers,
        )
        actions = [log["action"] for log in res.json()["items"]]
        assert actions == ["UPDATE", "CREATE"]

    def test_parent_from_other_project_rejected(self, client, manager_headers, project, make_user):
        """UT-WBS-01: 다른 프로젝트의 parent 거부."""
        other_customer = client.post(
            "/api/customers", json={"name": "다른고객사"}, headers=manager_headers
        ).json()
        pm = make_user("other-pm@test.com", role="manager")
        other = client.post(
            "/api/projects",
            json={
                "code": "PRJ-OTHER",
                "name": "다른 프로젝트",
                "customer_id": other_customer["id"],
                "project_type": "SW",
                "manager_id": pm.id,
            },
            headers=manager_headers,
        ).json()
        other_wbs = _create_wbs(client, manager_headers, other["id"], name="남의작업").json()

        res = _create_wbs(
            client, manager_headers, project["id"], parent_id=other_wbs["id"]
        )
        assert res.status_code == 404

    def test_self_and_circular_parent_rejected(self, client, manager_headers, project):
        """UT-WBS-02: 자기 자신·순환 참조 parent 거부."""
        pid = project["id"]
        a = _create_wbs(client, manager_headers, pid, name="A").json()
        b = _create_wbs(client, manager_headers, pid, name="B", parent_id=a["id"]).json()

        res = client.patch(
            f"/api/projects/{pid}/wbs/{a['id']}",
            json={"parent_id": a["id"]},
            headers=manager_headers,
        )
        assert res.status_code == 400
        assert res.json()["code"] == "INVALID_PARENT"

        res = client.patch(
            f"/api/projects/{pid}/wbs/{a['id']}",
            json={"parent_id": b["id"]},
            headers=manager_headers,
        )
        assert res.status_code == 400
        assert res.json()["code"] == "CIRCULAR_PARENT"

    def test_progress_100_marks_done(self, client, manager_headers, project):
        """UT-WBS-03: 진척률 100 → DONE, 범위 초과 거부."""
        pid = project["id"]
        item = _create_wbs(client, manager_headers, pid, progress=100).json()
        assert item["status"] == "DONE"

        item2 = _create_wbs(client, manager_headers, pid, name="작업2").json()
        res = client.patch(
            f"/api/projects/{pid}/wbs/{item2['id']}",
            json={"progress": 100},
            headers=manager_headers,
        )
        assert res.json()["status"] == "DONE"

        res = _create_wbs(client, manager_headers, pid, name="작업3", progress=150)
        assert res.status_code == 422

    def test_delay_computation(self, client, manager_headers, project):
        """UT-WBS-04: 종료일 경과 & 미완료 → 지연, 완료면 지연 아님."""
        pid = project["id"]
        delayed = _create_wbs(
            client, manager_headers, pid, name="지연작업", end_date=YESTERDAY
        ).json()
        assert delayed["is_delayed"] is True

        done = _create_wbs(
            client, manager_headers, pid, name="완료작업",
            end_date=YESTERDAY, progress=100,
        ).json()
        assert done["is_delayed"] is False

        future = _create_wbs(
            client, manager_headers, pid, name="미래작업", end_date=TOMORROW
        ).json()
        assert future["is_delayed"] is False

    def test_deactivate_cascades_children(self, client, manager_headers, project):
        """UT-WBS-05: 비활성화 시 하위 항목 함께 비활성화."""
        pid = project["id"]
        parent = _create_wbs(client, manager_headers, pid, name="부모").json()
        child = _create_wbs(
            client, manager_headers, pid, name="자식", parent_id=parent["id"]
        ).json()
        grandchild = _create_wbs(
            client, manager_headers, pid, name="손자", parent_id=child["id"]
        ).json()

        res = client.patch(
            f"/api/projects/{pid}/wbs/{parent['id']}/deactivate",
            headers=manager_headers,
        )
        assert res.status_code == 204

        items = client.get(f"/api/projects/{pid}/wbs", headers=manager_headers).json()
        remaining_ids = {i["id"] for i in items}
        assert not remaining_ids & {parent["id"], child["id"], grandchild["id"]}

    def test_member_cannot_create(self, client, auth_headers, project):
        """IT-11: member가 WBS 등록 시도 → 403."""
        headers = auth_headers("member")
        res = _create_wbs(client, headers, project["id"])
        assert res.status_code == 403


class TestAssigneePermission:
    def test_assignee_updates_own_progress(self, client, auth_headers, project, manager_headers):
        """IT-10: 담당자 본인 진척률 수정 성공, 타 필드·타인 항목 403."""
        pid = project["id"]
        assignee_headers = auth_headers("member", email="assignee@test.com")
        me = client.get("/api/auth/me", headers=assignee_headers).json()

        mine = _create_wbs(
            client, manager_headers, pid, name="내작업", assignee_id=me["id"]
        ).json()
        others = _create_wbs(client, manager_headers, pid, name="남의작업").json()

        # 본인 항목 진척률·상태 수정 성공
        res = client.patch(
            f"/api/projects/{pid}/wbs/{mine['id']}",
            json={"progress": 50, "status": "IN_PROGRESS"},
            headers=assignee_headers,
        )
        assert res.status_code == 200
        assert res.json()["progress"] == 50

        # 본인 항목이라도 이름 수정은 403
        res = client.patch(
            f"/api/projects/{pid}/wbs/{mine['id']}",
            json={"name": "이름변경"},
            headers=assignee_headers,
        )
        assert res.status_code == 403
        assert res.json()["code"] == "FIELD_NOT_ALLOWED"

        # 타인 항목 수정은 403
        res = client.patch(
            f"/api/projects/{pid}/wbs/{others['id']}",
            json={"progress": 10},
            headers=assignee_headers,
        )
        assert res.status_code == 403
        assert res.json()["code"] == "NOT_ASSIGNEE"


class TestMilestone:
    def test_milestone_flow(self, client, manager_headers, project):
        """UT-MS-01: 등록 → 지연 판정 → 달성 처리."""
        pid = project["id"]
        delayed = client.post(
            f"/api/projects/{pid}/milestones",
            json={"name": "시제품 완성", "due_date": YESTERDAY},
            headers=manager_headers,
        ).json()
        assert delayed["is_delayed"] is True
        assert delayed["status"] == "PENDING"

        res = client.patch(
            f"/api/projects/{pid}/milestones/{delayed['id']}/achieve",
            headers=manager_headers,
        )
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "ACHIEVED"
        assert body["achieved_date"] == TODAY.isoformat()
        assert body["is_delayed"] is False

        # 중복 달성 처리 거부
        res = client.patch(
            f"/api/projects/{pid}/milestones/{delayed['id']}/achieve",
            headers=manager_headers,
        )
        assert res.status_code == 400

    def test_member_cannot_create_milestone(self, client, auth_headers, project):
        headers = auth_headers("member")
        res = client.post(
            f"/api/projects/{project['id']}/milestones",
            json={"name": "MS", "due_date": TOMORROW},
            headers=headers,
        )
        assert res.status_code == 403


class TestScheduleSummary:
    def test_summary(self, client, manager_headers, project):
        """UT-SCH-01 / IT-12: 진척률 평균·지연 수 계산 (비활성 제외)."""
        pid = project["id"]
        _create_wbs(client, manager_headers, pid, name="w1", progress=100)
        _create_wbs(client, manager_headers, pid, name="w2", progress=50, end_date=YESTERDAY)
        excluded = _create_wbs(client, manager_headers, pid, name="w3", progress=0).json()
        client.patch(
            f"/api/projects/{pid}/wbs/{excluded['id']}/deactivate",
            headers=manager_headers,
        )
        client.post(
            f"/api/projects/{pid}/milestones",
            json={"name": "지연MS", "due_date": YESTERDAY},
            headers=manager_headers,
        )
        client.post(
            f"/api/projects/{pid}/milestones",
            json={"name": "정상MS", "due_date": TOMORROW},
            headers=manager_headers,
        )

        res = client.get(f"/api/projects/{pid}/schedule/summary", headers=manager_headers)
        assert res.status_code == 200
        summary = res.json()
        assert summary == {
            "progress": 75.0,
            "wbs_total": 2,
            "wbs_delayed": 1,
            "milestone_total": 2,
            "milestone_delayed": 1,
        }

    def test_empty_project_summary(self, client, manager_headers, project):
        res = client.get(
            f"/api/projects/{project['id']}/schedule/summary", headers=manager_headers
        )
        assert res.json()["progress"] == 0.0
