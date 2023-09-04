"""
Tests the routes for family management.

This uses a service mock and ensures each endpoint calls into the service.
"""
from fastapi.testclient import TestClient
from app.model.family import FamilyDTO
import app.service.family as family_service
from unit_tests.helpers.family import create_family_dto


# --- GET


def test_get_all_families_returns_200(
    client: TestClient,
    mocker,
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    spy = mocker.spy(family_service, "all")
    response = client.get(
        "/api/v1/families",
    )
    assert response.status_code == 200
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "test"
    assert spy.call_count == 1


def test_get_family_returns_200(
    client: TestClient,
    mocker,
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    spy = mocker.spy(family_service, "get")
    response = client.get(
        "/api/v1/families/A.0.0.1",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == "A.0.0.1"
    assert spy.call_count == 1


def test_get_family_returns_404(
    client: TestClient,
    mocker,
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    spy = mocker.spy(family_service, "get")
    family_repo_mock.error = True
    response = client.get(
        "/api/v1/families/A.0.0.1",
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not found: A.0.0.1"
    assert spy.call_count == 1


# --- SEARCH


def test_search_family_returns_200(
    client: TestClient,
    mocker,
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    spy = mocker.spy(family_service, "search")
    response = client.get(
        "/api/v1/families/?q=anything",
    )
    assert response.status_code == 200
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"
    assert spy.call_count == 1


def test_search_family_returns_404(
    client: TestClient,
    mocker,
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    spy = mocker.spy(family_service, "search")
    family_repo_mock.error = True
    response = client.get(
        "/api/v1/families/?q=empty",
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Families not found for term: empty"
    assert spy.call_count == 1


# --- UPDATE


def test_update_family_returns_200(
    client: TestClient,
    mocker,
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    spy = mocker.spy(family_service, "update")
    new_data = create_family_dto("a.b.c.d").dict()
    response = client.put("/api/v1/families", json=new_data)
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == "a.b.c.d"
    assert spy.call_count == 1


def test_update_family_returns_404(
    client: TestClient,
    mocker,
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    spy = mocker.spy(family_service, "update")
    family_repo_mock.error = True
    new_data = create_family_dto("a.b.c.d").dict()
    response = client.put("/api/v1/families", json=new_data)
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not updated: a.b.c.d"
    assert spy.call_count == 1


# --- CREATE


def test_create_family_returns_200(
    client: TestClient,
    mocker,
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    spy = mocker.spy(family_service, "create")
    new_data = create_family_dto("a.b.c.d").dict()
    response = client.post("/api/v1/families", json=new_data)
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == "a.b.c.d"
    assert spy.call_count == 1


def test_create_family_returns_404(
    client: TestClient,
    mocker,
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    spy = mocker.spy(family_service, "create")
    new_data: FamilyDTO = create_family_dto("a.b.c.d")
    family_repo_mock.error = True
    response = client.post("/api/v1/families", json=new_data.dict())
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not created: a.b.c.d"
    assert spy.call_count == 1


# --- DELETE


def test_delete_family_returns_200(
    client: TestClient,
    mocker,
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    spy = mocker.spy(family_service, "delete")
    response = client.delete("/api/v1/families/a.b.c.d")
    assert response.status_code == 200
    assert spy.call_count == 1


def test_delete_family_returns_404(
    client: TestClient,
    mocker,
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    spy = mocker.spy(family_service, "delete")
    family_repo_mock.error = True
    response = client.delete("/api/v1/families/a.b.c.d")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not deleted: a.b.c.d"
    assert spy.call_count == 1
