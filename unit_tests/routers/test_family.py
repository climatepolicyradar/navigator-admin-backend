"""
Tests the routes for family management.

This uses a service mock and ensures each endpoint calls into the service.
"""
from fastapi import status
from fastapi.testclient import TestClient
from app.model.family import FamilyDTO

from unit_tests.helpers.family import create_family_dto


def test_get_all_families_uses_service_200(
    client: TestClient, family_service_mock, user_header_token
):
    response = client.get("/api/v1/families", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "test"
    assert family_service_mock.all.call_count == 1


def test_get_family_uses_service_200(
    client: TestClient, family_service_mock, user_header_token
):
    response = client.get("/api/v1/families/import_id", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "import_id"
    assert family_service_mock.get.call_count == 1


def test_get_family_uses_service_404(
    client: TestClient, family_service_mock, user_header_token
):
    response = client.get("/api/v1/families/missing", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not found: missing"
    assert family_service_mock.get.call_count == 1


def test_search_family_uses_service_200(
    client: TestClient, family_service_mock, user_header_token
):
    response = client.get("/api/v1/families/?q=anything", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"
    assert family_service_mock.search.call_count == 1


def test_search_family_uses_service_404(
    client: TestClient, family_service_mock, user_header_token
):
    response = client.get("/api/v1/families/?q=empty", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Families not found for term: empty"
    assert family_service_mock.search.call_count == 1


def test_update_family_uses_service_200(
    client: TestClient, family_service_mock, user_header_token
):
    new_data = create_family_dto("fam1").dict()
    response = client.put("/api/v1/families", json=new_data, headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "fam1"
    assert family_service_mock.update.call_count == 1


def test_update_family_uses_service_404(
    client: TestClient, family_service_mock, user_header_token
):
    new_data = create_family_dto("missing").dict()
    response = client.put("/api/v1/families", json=new_data, headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not updated: missing"
    assert family_service_mock.update.call_count == 1


def test_create_family_uses_service_200(
    client: TestClient, family_service_mock, user_header_token
):
    new_data = create_family_dto("fam1").dict()
    response = client.post("/api/v1/families", json=new_data, headers=user_header_token)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["import_id"] == "fam1"
    assert family_service_mock.create.call_count == 1


def test_create_family_uses_service_404(
    client: TestClient, family_service_mock, user_header_token
):
    new_data: FamilyDTO = create_family_dto("fam1")
    new_data.import_id = "missing"
    response = client.post(
        "/api/v1/families", json=new_data.dict(), headers=user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not created: missing"
    assert family_service_mock.create.call_count == 1


def test_delete_family_uses_service_200(
    client: TestClient, family_service_mock, admin_user_header_token
):
    response = client.delete("/api/v1/families/fam1", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert family_service_mock.delete.call_count == 1


def test_delete_family_fails_if_not_admin(
    client: TestClient, family_service_mock, user_header_token
):
    response = client.delete("/api/v1/families/fam1", headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert family_service_mock.delete.call_count == 0


def test_delete_family_uses_service_404(
    client: TestClient, family_service_mock, admin_user_header_token
):
    response = client.delete(
        "/api/v1/families/missing", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not deleted: missing"
    assert family_service_mock.delete.call_count == 1
