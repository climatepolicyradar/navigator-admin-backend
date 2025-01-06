"""
Tests the routes for family management.

This uses a service mock and ensures each endpoint calls into the service.
"""

from fastapi import status
from fastapi.testclient import TestClient


def test_get_all_when_ok(client: TestClient, family_service_mock, user_header_token):
    response = client.get("/api/v1/families", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["import_id"] == "test"
    assert family_service_mock.all.call_count == 1


def test_get_when_ok(client: TestClient, family_service_mock, user_header_token):
    response = client.get("/api/v1/families/import_id", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "import_id"
    assert family_service_mock.get.call_count == 1


def test_get_when_not_found(client: TestClient, family_service_mock, user_header_token):
    family_service_mock.missing = True
    response = client.get("/api/v1/families/fam1", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not found: fam1"
    assert family_service_mock.get.call_count == 1


def test_get_endpoint_returns_families_with_multiple_geographies(
    client: TestClient, family_service_mock, user_header_token
):
    response = client.get("/api/v1/families", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert family_service_mock.all.call_count == 1
    for item in data:
        keys = item.keys()
        assert "geography" in keys
        assert "geographies" in keys
        assert item["geographies"] == ["CHN", "BRB", "BHS"]
