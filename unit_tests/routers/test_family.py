"""
Tests the routes for family management.

This uses a service mock and ensures each endpoint calls into the service.
"""
from fastapi.testclient import TestClient
from app.model.family import FamilyDTO
import app.service.family as family_service
from unit_tests.mocks.family_service import create_family_dto


def test_get_all_families_uses_service_200(client: TestClient, family_service_mock):
    response = client.get(
        "/api/v1/families",
    )
    assert response.status_code == 200
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "test"
    assert family_service.all.call_count == 1


def test_get_family_uses_service_200(client: TestClient, family_service_mock):
    response = client.get(
        "/api/v1/families/import_id",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == "import_id"
    assert family_service.get.call_count == 1


def test_get_family_uses_service_404(client: TestClient, family_service_mock):
    response = client.get(
        "/api/v1/families/missing",
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not found: missing"
    assert family_service.get.call_count == 1


def test_search_family_uses_service_200(client: TestClient, family_service_mock):
    response = client.get(
        "/api/v1/families/?q=anything",
    )
    assert response.status_code == 200
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"
    assert family_service.search.call_count == 1


def test_search_family_uses_service_404(client: TestClient, family_service_mock):
    response = client.get(
        "/api/v1/families/?q=empty",
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Families not found for term: empty"
    assert family_service.search.call_count == 1


def test_update_family_uses_service_200(client: TestClient, family_service_mock):
    new_data = create_family_dto("fam1").dict()
    response = client.put("/api/v1/families", json=new_data)
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == "fam1"
    assert family_service.update.call_count == 1


def test_update_family_uses_service_404(client: TestClient, family_service_mock):
    new_data = create_family_dto("missing").dict()
    response = client.put("/api/v1/families", json=new_data)
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not updated: missing"
    assert family_service.update.call_count == 1


def test_create_family_uses_service_200(client: TestClient, family_service_mock):
    new_data = create_family_dto("fam1").dict()
    response = client.post("/api/v1/families", json=new_data)
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == "fam1"
    assert family_service.create.call_count == 1


def test_create_family_uses_service_404(client: TestClient, family_service_mock):
    new_data: FamilyDTO = create_family_dto("fam1")
    new_data.import_id = "missing"
    response = client.post("/api/v1/families", json=new_data.dict())
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not created: missing"
    assert family_service.create.call_count == 1


def test_delete_family_uses_service_200(client: TestClient, family_service_mock):
    response = client.delete("/api/v1/families/fam1")
    assert response.status_code == 200
    assert family_service.delete.call_count == 1


def test_delete_family_uses_service_404(client: TestClient, family_service_mock):
    response = client.delete("/api/v1/families/missing")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not deleted: missing"
    assert family_service.delete.call_count == 1
