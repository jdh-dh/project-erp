"""UT-CUST-01, IT-04: 고객사 관리 시험."""


def _create_customer(client, headers, name="테스트고객사"):
    res = client.post(
        "/api/customers",
        json={"name": name, "business_no": "123-45-67890", "address": "서울시"},
        headers=headers,
    )
    assert res.status_code == 201, res.text
    return res.json()


class TestCustomerCrud:
    def test_create_and_get(self, client, auth_headers):
        headers = auth_headers("manager")
        customer = _create_customer(client, headers)
        res = client.get(f"/api/customers/{customer['id']}", headers=headers)
        assert res.status_code == 200
        assert res.json()["name"] == "테스트고객사"

    def test_update(self, client, auth_headers):
        headers = auth_headers("manager")
        customer = _create_customer(client, headers)
        res = client.patch(
            f"/api/customers/{customer['id']}",
            json={"address": "부산시"},
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json()["address"] == "부산시"

    def test_contact_flow(self, client, auth_headers):
        """IT-04: 고객사 등록 → 담당자 추가 → 상세 조회에 담당자 포함."""
        headers = auth_headers("manager")
        customer = _create_customer(client, headers)

        res = client.post(
            f"/api/customers/{customer['id']}/contacts",
            json={
                "name": "김담당",
                "position": "과장",
                "phone": "010-1234-5678",
                "email": "kim@customer.com",
            },
            headers=headers,
        )
        assert res.status_code == 201
        contact_id = res.json()["id"]

        res = client.get(f"/api/customers/{customer['id']}", headers=headers)
        contacts = res.json()["contacts"]
        assert len(contacts) == 1
        assert contacts[0]["name"] == "김담당"

        res = client.patch(
            f"/api/customers/{customer['id']}/contacts/{contact_id}",
            json={"position": "차장"},
            headers=headers,
        )
        assert res.status_code == 200
        assert res.json()["position"] == "차장"

    def test_deactivate(self, client, auth_headers):
        headers = auth_headers("manager")
        customer = _create_customer(client, headers)
        res = client.patch(
            f"/api/customers/{customer['id']}/deactivate", headers=headers
        )
        assert res.status_code == 200
        assert res.json()["is_active"] is False

    def test_member_cannot_create(self, client, auth_headers):
        headers = auth_headers("member")
        res = client.post(
            "/api/customers", json={"name": "고객사"}, headers=headers
        )
        assert res.status_code == 403

    def test_search_by_name(self, client, auth_headers):
        headers = auth_headers("manager")
        _create_customer(client, headers, name="알파전자")
        _create_customer(client, headers, name="베타시스템")
        res = client.get("/api/customers?q=알파", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "알파전자"

    def test_not_found(self, client, auth_headers):
        headers = auth_headers("manager")
        res = client.get("/api/customers/99999", headers=headers)
        assert res.status_code == 404
